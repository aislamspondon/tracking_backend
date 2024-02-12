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


@api_view(['POST'])
@permission_classes([IsAdminUser])
def CreateTracking(request):
    data = request.data
    trackCreate = Tracking.objects.create(
        tracking_number = data['tracking_number'],
        order_number = data['order_number'],
    )
    serializer = TrackingSerializer(trackCreate)
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
# @permission_classes([IsAdminUser])
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
    print("Enter APi")
    track = TrackAPI()
    # print("Out From APi ", track)
    tracking_all_details = track.TrackingOrder(trackingId)
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
        return Response({"message": "Order not exits"}, status=status.HTTP_404_NOT_FOUND)
    tracking = qs.first()
    trackingId = tracking.tracking_number
    blacklist = BlackListed.objects.all()
    blacklisted_word = [{'word': q.word, 'replace_word': q.replace_word } for q in blacklist]
    track = TrackAPI()
    tracking_all_details = track.TrackingOrder(trackingId)
    tracking_status = tracking_all_details['status']
    # Create a regular expression pattern from the dictionary keys
    pattern = '|'.join(r'\b{}\b'.format(re.escape(d['word'])) for d in blacklisted_word)
    # Replace the words in the array with the corresponding replacement words
    replace_tracking_status = [re.sub(pattern, lambda m: next((d['replace_word'] for d in blacklisted_word if d['word'] == m.group(0))), item['status']) for item in tracking_status]
    for i,trackStatus in enumerate(tracking_all_details['status']):
        trackStatus['status'] = replace_tracking_status[i]
    serializer = TrackingStatusSerializer(tracking_all_details)
    return Response(serializer.data, status=status.HTTP_200_OK)

