import json
import time

import requests


class TrackAPI:
    ship24Url = "https://api.ship24.com/public/v1/trackers"
    apiKey = "apik_CjnUCgyp4aJBRYbArHGb3kCYeBvYhI"

    def TrackingOrder(self, trackingNumber):
        headers = {
        "Authorization": f"Bearer {self.apiKey}",
        "Content-Type": "application/json; charset=utf-8"
        }
        payload = {"trackingNumber": trackingNumber}
        response = requests.post(self.ship24Url, headers=headers, data=json.dumps(payload))
        data = response.json()
        tracker = data['data']
        trackerId = tracker['tracker']['trackerId']
        trackerUrl = f"https://api.ship24.com/public/v1/trackers/{trackerId}/results"
        track_response = requests.get(trackerUrl, headers=headers)
        track_response_json = json.loads(track_response.text)
        status = track_response_json['data']['trackings'][0]
        all_track_status = status['events']
        estimatedDate = status['shipment']['delivery']['estimatedDeliveryDate']
        eventStatus = [{'status': track_status['status'], 'date': track_status['datetime']} for track_status in all_track_status]
        delivery = ({'estimateDelivery': estimatedDate, 'status': eventStatus})
        return delivery
