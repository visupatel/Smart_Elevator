from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .validation import isValid_type
from .models import UserRequest, Elevator

def assign_elevator(source_floor, direction):

    elevators = Elevator.objects.all()

    best_elevator = None
    min_distance = float("inf")    # infinity

    for elevator in elevators:
        
        # ignore currently moving 
        if elevator.is_moving:
            continue

        if elevator.is_emergency:
            continue

        distance = abs(elevator.current_floor - source_floor)

        if elevator.direction != "IDLE":
            if elevator.direction != direction:
                distance += 100

        if distance < min_distance:
            min_distance = distance
            best_elevator = elevator

    return best_elevator


@api_view(['POST']) 
def add_request(request): 

    try:
        source_floor = request.data.get("source_floor") 
        destination_floor = request.data.get("destination_floor") 

        if not source_floor:
            return Response({ 
                "status": "failed", 
                "message": "'source_floor' must be required" 
                },
                status=status.HTTP_400_BAD_REQUEST
                )
        
        if not destination_floor:
            return Response({ 
                "status": "failed", 
                "message": "'destination_floor' must be required" 
                },
                status=status.HTTP_400_BAD_REQUEST
                )
        
        source_floor = isValid_type(int,source_floor,"integer","source_floor")
        destination_floor = isValid_type(int,destination_floor,"integer","destination_floor")
        
        # check source floor and destination floor not be same
        if source_floor == destination_floor: 
            return Response({ 
                "status": "failed", 
                "message": "source and destination cannot be same" 
                },
                status=status.HTTP_400_BAD_REQUEST
                ) 
        
        # source floor and destination floor always between building floor
        if source_floor < 0 or source_floor > 10:
            return Response({
                "status":"failed",
                "message":"source_floor must be between 0 and 10"
            }, 
            status=status.HTTP_400_BAD_REQUEST
            )

        if destination_floor < 0 or destination_floor > 10:
            return Response({
                "status":"failed",
                "message":"destination_floor must be between 0 and 10"
            }, 
            status=status.HTTP_400_BAD_REQUEST
            )
        
        # Deside direction 
        if destination_floor > source_floor:
            direction = "UP"
        else:
            direction = "DOWN"

        elevator = assign_elevator(source_floor, direction)
        
        if not elevator:
            return Response({
                "status": "failed",
                "message": "No available elevator (all are busy or emergency)"
            }, 
            status=status.HTTP_400_BAD_REQUEST
            )
        
        elevatorreq = UserRequest.objects.create(
            source_floor=source_floor, 
            destination_floor=destination_floor, 
            direction=direction,
            elevator=elevator,
            status="PENDING" ,
            ) 
        
        return Response({ 
            "status": "success", 
            "message":"user request added successfully",
            "request_id": elevatorreq.id, 
            "souce_floor":source_floor,
            "destination_floor":destination_floor,
            "direction": direction,
            "assigned_elevator": elevator.name 
            },
            status=status.HTTP_201_CREATED
            )
    
    except ValueError as e:
        return Response({
            "status":"failed",
            "message":str(e)
        },
        status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        return Response({
            "status":"error",
            "message":str(e)
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    

@api_view(['POST'])
def move_elevator(request):
    try:
        
        elevators = Elevator.objects.all()
        results = []
        for elevator in elevators:
            if elevator.is_emergency:
                continue

            requests = UserRequest.objects.filter(
                elevator=elevator,
                status="PENDING"
            ).order_by("source_floor")

            if not requests.exists():
                continue

            current = elevator.current_floor

            up = requests.filter(source_floor__gte=current).order_by("source_floor")
            down = requests.filter(source_floor__lt=current).order_by("-source_floor")

            # take up requests if up request completed then take down request
            if elevator.direction in ["UP", "IDLE"]:
                queue = list(up) + list(down)
                elevator.direction = "UP"
            
            # take down requests if down request completed then take up request
            else:
                queue = list(down) + list(up)
                elevator.direction = "DOWN"

            movement_log = []

            for req in queue:

                # move to source
                elevator.current_floor = req.source_floor
                elevator.save()

                # pickup
                req.status = "COMPLETED"
                req.save()

                # move to destination
                elevator.current_floor = req.destination_floor
                elevator.save()

                movement_log.append({
                    "request_id": req.id,
                    "from": req.source_floor,
                    "to": req.destination_floor,
                    "direction":req.direction
                })

            elevator.is_moving = False
            elevator.direction = "IDLE"
            elevator.save()

            results.append({
                "elevator": elevator.name,
                "final_floor": elevator.current_floor,
                "movements": movement_log
            })
        
        if not results:
            return Response({
                "status": "failed",
                "message":"No elevator moving because no request arrived or all elevators are on emergency mode.",
                },
                status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response({
            "status": "success",
            "message":"elevator moving",
            "data": results
        },
        status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def emergency_on(request):
    try:
        elevator_id = request.data.get("elevator_id")

        if not elevator_id:
            return Response({
                "status": "failed",
                "message": "'elevator_id' must be required"
            }, 
            status=status.HTTP_400_BAD_REQUEST
            )
        
        elevator_id = isValid_type(int,elevator_id,"integer","elevator_id")
        
        # emergency mode on
        elevator = Elevator.objects.get(id=elevator_id)
        elevator.is_emergency=True
        elevator.is_moving=False
        elevator.direction="IDLE"
        elevator.save()

        return Response({
            "status": "success",
            "message": f"Elevator '{elevator.name}' Emergency mode ON"
        },
        status=status.HTTP_200_OK
        )
    
    except ValueError as e:
        return Response({
            "status":"failed",
            "message":str(e)
        },
        status=status.HTTP_400_BAD_REQUEST
        )
    
    except Elevator.DoesNotExist:
        return Response({
            "status":"failed",
            "message":"No such elevator, only 1,2 and 3 elevators"
        },
        status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        return Response({
            "status":"error",
            "message":str(e),
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def emergency_off(request):   
    try:
        elevator_id = request.data.get("elevator_id")

        if not elevator_id:
            return Response({
                "status": "failed",
                "message": "'elevator_id' must be required"
            }, 
            status=status.HTTP_400_BAD_REQUEST
            )
        
        elevator_id = isValid_type(int,elevator_id,"integer","elevator_id")

        # emergency mode off
        elevator = Elevator.objects.get(id=elevator_id)
        elevator.is_emergency=False
        elevator.save()
        
        return Response({
            "status": "success",
            "message": f"Elevator '{elevator.name}' Emergency mode OFF"
        },
        status=status.HTTP_200_OK
        )
    
    except ValueError as e:
        return Response({
            "status":"failed",
            "message":str(e)
        },
        status=status.HTTP_400_BAD_REQUEST
        )
    
    except Elevator.DoesNotExist:
        return Response({
            "status":"failed",
            "message":"No such elevator, only 1,2 and 3 elevators"
        },
        status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        return Response({
            "status":"error",
            "message":str(e),
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
