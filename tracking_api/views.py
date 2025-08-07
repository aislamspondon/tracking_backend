import re

from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from tracking_api.models import BlackListed, Tracking
from tracking_api.serializers import (BlacklistedSerializer,
                                      TrackingSerializer,
                                      TrackingStatusSerializer)
from tracking_api.trackingProduct import TrackAPI
import pandas as pd


def create_track_dataset(file_path):
    try:
        data = pd.read_excel(file_path)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return False

    # print("Columns in the Excel file:", data.columns.tolist())

    for index, row in data.iterrows():
        try:
            if 'TrackingNum' not in data.columns or 'OrderNumber' not in data.columns:
                print("Required columns are not present in the Excel file.")
                if 'Tracking Number' not in data.columns or 'Reference Number' not in data.columns:
                    return False
                TrackingNum = row['Tracking Number']
                OrderNumber = row['Reference Number'][3:]
            else:
                TrackingNum = row['TrackingNum']
                OrderNumber = row['OrderNumber']
            Tracking.objects.create(
                tracking_number = TrackingNum,
                order_number = OrderNumber,
            )
        except KeyError as e:
            print(f"Missing column in row {index}: {e}")
            continue

    return True




@api_view(['POST'])
def upload_tracking(request):
    data = request.data  # expecting a JSON list of tracking items

    if not isinstance(data, list):
        return Response({"error": "Expected a list of tracking items"}, status=status.HTTP_400_BAD_REQUEST)

    created = []
    skipped = []

    for item in data:
        try:
            tracking_number = item['tracking_no']
            order_number = item['order_id']

            # Check if tracking_number already exists
            if Tracking.objects.filter(tracking_number=tracking_number).exists():
                skipped.append({
                    "tracking_number": tracking_number,
                    "reason": "Already exists"
                })
                continue

            tracking = Tracking.objects.create(
                tracking_number=tracking_number,
                order_number=order_number
            )

            created.append({
                "_id": tracking._id,
                "tracking_number": tracking.tracking_number,
                "order_number": tracking.order_number
            })

        except KeyError as e:
            return Response({"error": f"Missing key is: {e}"}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        "message": "Tracking upload completed",
        "created": created,
        "skipped": skipped
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def CreateTracking(request):
    data = request.data
    
    track_api = TrackAPI()
    tracking_id = track_api.postAfterShipTracking(data['tracking_number'])
    # tracking_id = track_api.postAfterShipTrackingVersion2(data['tracking_number'])
    if tracking_id is False:
        return Response({"error": "Failed to create tracking ID"}, status=status.HTTP_400_BAD_REQUEST)
    


    trackCreate = Tracking.objects.create(
        tracking_id = tracking_id,
        tracking_number = data['tracking_number'],
        order_number = data['order_number'],
    )
    # print("Track Created", trackCreate)
    serializer = TrackingSerializer(trackCreate)
    print(serializer.data, "Track Created")
    return Response(data=serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def getAllTracking(request):
    track = Tracking.objects.all()
    search = request.query_params.get('search')
    if search:
        track = track.filter(field_icontains=search)
    serializer = TrackingSerializer(track, many=True)
    return Response(data=serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def getSingleTracking(request, tracking_id):
    track = Tracking.objects.get(_id=tracking_id)
    serializer = TrackingSerializer(track, many=False)
    return Response(data=serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAdminUser])
def updateTracking(request, tracking_id):
    data = request.data
    qs = Tracking.objects.filter(_id=tracking_id)
    track = qs.first()
    if not qs.exists():
        return Response({"message": "Track not exits"}, status=status.HTTP_404_NOT_FOUND)
    track.tracking_number = data['tracking_number']
    track.order_number = data['order_number']
    track.save()
    serializer = TrackingSerializer(track, many=False)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def deletetracking(request, tracking_id):
    qs = Tracking.objects.filter(_id=tracking_id)
    track = qs.first()
    if not qs.exists():
        return Response({"message": "Track not exits"}, status=status.HTTP_404_NOT_FOUND)
    track.delete()
    return Response({"message": "Track Deleted"}, status=status.HTTP_200_OK)



@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def deletetracking_list(request):
    data = request.data
    user = request.user
    if 'track_data_list' not in request.data:
        return Response({"error": "Please Enter Trackdata"}, status= status.HTTP_400_BAD_REQUEST)
    track_data = data['track_data_list']
    if len(track_data) > 0:
        for tracking_id in track_data:
            qs = Tracking.objects.filter(_id = tracking_id)
            track = qs.first()
            track.delete()
            print("Delete")

    return Response({"message": "Delete Successfully "}, status=status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes([IsAdminUser])
def CreateBlacklisted(request):
    data = request.data
    blacklistCreate = BlackListed.objects.create(
        word = data['word'],
        replace_word = data['replace_word'],
    )
    serializer = BlacklistedSerializer(blacklistCreate)
    return Response(data=serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def getAllBlackList(request):
    blacklist = BlackListed.objects.all()
    search = request.query_params.get('search')
    if search:
        blacklist = blacklist.filter(field_icontains=search)
    serializer = BlacklistedSerializer(blacklist, many=True)
    return Response(data=serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def getSingleBlacklisted(request, blacklist_id):
    blacklist = BlackListed.objects.get(id=blacklist_id)
    serializer = BlacklistedSerializer(blacklist, many=False)
    return Response(data=serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAdminUser])
def updateBlacklisted(request, blacklist_id):
    data = request.data
    qs = BlackListed.objects.filter(id=blacklist_id)
    blacklist = qs.first()
    if not qs.exists():
        return Response({"message": "Word not exits"}, status=status.HTTP_404_NOT_FOUND)
    blacklist.word = data['word']
    blacklist.replace_word = data['replace_word']
    blacklist.save()
    serializer = BlacklistedSerializer(blacklist, many=False)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def deleteBlacklisted(request, blacklist_id):
    qs = BlackListed.objects.filter(id=blacklist_id)
    blacklist = qs.first()
    if not qs.exists():
        return Response({"message": "Word not exits"}, status=status.HTTP_404_NOT_FOUND)
    blacklist.delete()
    return Response({"message": "Blacklisted Word Deleted"}, status=status.HTTP_200_OK)

@api_view(['POST'])
def trackOrder(request):
    order_number = request.data['order_number']
    qs = Tracking.objects.filter(order_number=order_number)
    if not qs.exists():
        return Response({"message": "Order not exits"}, status=status.HTTP_404_NOT_FOUND)
    tracking = qs.first()
    trackingId = tracking.tracking_number
    blacklist = BlackListed.objects.all()
    # print(trackingId)
    blacklisted_word = [{'word': q.word, 'replace_word': q.replace_word } for q in blacklist]
    track = TrackAPI()
    # print("Out From APi ", track)
    # tracking_all_details = track.TrackingOrder(trackingId)
    tracking_all_details = track.AftershipTracking(trackingId)
    tracking_status = tracking_all_details['status']
    # Create a regular expression pattern from the dictionary keys
    pattern = '|'.join(r'\b{}\b'.format(re.escape(d['word'])) for d in blacklisted_word)
    # Replace the words in the array with the corresponding replacement words
    replace_tracking_status = [re.sub(pattern, lambda m: next((d['replace_word'] for d in blacklisted_word if d['word'] == m.group(0))), item['status']) for item in tracking_status]
    for i,trackStatus in enumerate(tracking_all_details['status']):
        trackStatus['status'] = replace_tracking_status[i]
    serializer = TrackingStatusSerializer(tracking_all_details)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def trackingOrderDetails(request, order_number):
    qs = Tracking.objects.filter(order_number=order_number)
    if not qs.exists():
        return Response({"message": "Unable to locate order, please contact Customer Service at help@valleyhatchery.com."}, status=status.HTTP_404_NOT_FOUND)
    trackingInfo = []
    for tracking in qs:
        trackingId = tracking.tracking_id
        blacklist = BlackListed.objects.all()
        blacklisted_word = [{'word': q.word, 'replace_word': q.replace_word } for q in blacklist]
        track = TrackAPI()
        # tracking_all_details = track.TrackingOrder(trackingId)
        # tracking_all_details = track.AfterShipTrackingVersion2(trackingId)
        tracking_all_details = track.AftershipTracking(trackingId)
        print("-0-------------------------------------------------------------")
        print("Tracking All Details:", tracking_all_details)
        if 'status' in tracking_all_details:
            tracking_status = tracking_all_details['status']
            print("Tracking Status:", tracking_status)
        else:
            print("No tracking status available")
            # Handle the case where status is not available
            tracking_status = []
        # print("this is nothing to do ")
        # tracking_location = tracking_all_details['location']
        # print(tracking_location)
        # Create a regular expression pattern from the dictionary keys
        pattern = '|'.join(r'\b{}\b'.format(re.escape(d['word'])) for d in blacklisted_word)
        # Replace the words in the array with the corresponding replacement words
        replace_tracking_status = [re.sub(pattern, lambda m: next((d['replace_word'] for d in blacklisted_word if d['word'] == m.group(0))), str(item['status'])) for item in tracking_status]
        replace_tracking_location = [re.sub(pattern, lambda m: next((d['replace_word'] for d in blacklisted_word if d['word'] ==  m.group(0))), str(item['location'])) for item in tracking_status]
        for i,trackStatus in enumerate(tracking_status):
            trackStatus['status'] = replace_tracking_status[i]
            trackStatus['location'] = replace_tracking_location[i]
        serializer = TrackingStatusSerializer(tracking_all_details)

        trackingInfo.append(serializer.data)
        # print("Tracking Info", trackingInfo)
    return Response(trackingInfo, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def upload_track_csv(request):
    file = request.FILES.get('file')
    if  file == None:
        return Response({"error": "Please Input Your File"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        create = create_track_dataset(file_path=file)
        # create = create_broker_dataset(obj.file)
        if create:
          return Response({"message": "Upload Track CSV"}, status=status.HTTP_200_OK)
        else:
            return Response({"error":'Error Occuard'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print("Error is :", e)
        return Response({"messsage": "Check your file please"}, status=status.HTTP_400_BAD_REQUEST)