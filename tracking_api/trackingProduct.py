import json
import requests


class TrackAPI:
    # Ship24 config
    ship24Url = "https://api.ship24.com/public/v1/trackers"
    ship24ApiKey = "apik_CjnUCgyp4aJBRYbArHGb3kCYeBvYhI"

    # AfterShip config
    aftershipUrl = "https://api.aftership.com/v4/trackings"
    aftershipApiKey = "asat_eea4c356e9de40fea4b47806fbd7dd9f"

    def TrackingOrder(self, trackingNumber):
        headers = {
            "Authorization": f"Bearer {self.ship24ApiKey}",
            "Content-Type": "application/json; charset=utf-8"
        }
        payload = {"trackingNumber": trackingNumber}

        try:
            response = requests.post(self.ship24Url, headers=headers, data=json.dumps(payload))
            data = response.json()
            tracker = data['data']
            trackerId = tracker['tracker']['trackerId']

            # Get tracking results
            trackerUrl = f"https://api.ship24.com/public/v1/trackers/{trackerId}/results"
            track_response = requests.get(trackerUrl, headers=headers)
            track_response_json = track_response.json()

            status = track_response_json['data']['trackings'][0]
            print("----------------------------------------------------------")
            print("Tracking Status Object:", status)
            print("----------------------------------------------------------")
            all_track_status = status['events']
            estimatedDate = status['shipment']['delivery']['estimatedDeliveryDate']

            eventStatus = [
                {
                    'status': track_status['status'],
                    'date': track_status['datetime'],
                    'location': track_status['location']
                }
                for track_status in all_track_status
            ]

            delivery = {
                'estimateDelivery': estimatedDate,
                'status': eventStatus
            }

            return delivery

        except Exception as e:
            return {"error": str(e)}

    def AftershipTracking(self, tracking_number, retry_count=0, max_retries=1):
        url = f"{self.aftershipUrl}/usps/{tracking_number}"
        headers = {
            "aftership-api-key": self.aftershipApiKey,
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            # Try to register tracking number if not found
            register_data = {
                "tracking": {
                    "tracking_number": tracking_number,
                    "carrier": "usps"
                }
            }
            requests.post(self.aftershipUrl, headers=headers, json=register_data)

            # Retry after registering, if allowed
            if retry_count < max_retries:
                return self.AftershipTracking(tracking_number, retry_count + 1, max_retries)
            else:
                return {"error": f"AfterShip: Failed after {max_retries + 1} attempts."}

        # Parse tracking info
        raw_data = response.json()
        tracking = raw_data["data"]["tracking"]

        formatted_output = {
            "data": {
                "trackings": [
                    {
                        "tracker": {
                            "trackerId": tracking.get("id"),
                            "trackingNumber": tracking.get("tracking_number"),
                            "shipmentReference": tracking.get("order_id"),
                            "courierCode": [tracking.get("slug")] if tracking.get("slug") else [],
                            "clientTrackerId": tracking.get("order_id_path"),
                            "isSubscribed": tracking.get("subscribed", False),
                            "isTracked": tracking.get("active", False),
                            "createdAt": tracking.get("created_at")
                        },
                        "shipment": {
                            "shipmentId": tracking.get("id"),
                            "statusCode": tracking.get("tag"),
                            "statusCategory": tracking.get("tag").split("_")[0].lower() if tracking.get("tag") else None,
                            "statusMilestone": tracking.get("subtag"),
                            "originCountryCode": tracking.get("origin_country_iso3"),
                            "destinationCountryCode": tracking.get("destination_country_iso3"),
                            "delivery": {
                                "estimatedDeliveryDate": tracking.get("expected_delivery")
                            },
                        },
                        "events": tracking.get("checkpoints", [])
                    }
                ]
            }
        }

        status = formatted_output['data']['trackings'][0]
        try:

          status = formatted_output['data']['trackings'][0]

          for event in status['events']:
            event['status'] = event.pop('message')
            event['datetime'] = event.pop('checkpoint_time')
          print("Tracking Status Object:", status)
          all_track_status = status.get('events', [])
          estimatedDate = status.get('shipment', {}).get('delivery', {}).get('estimatedDeliveryDate', None)

          eventStatus = [
              {
                  'status': track_status.get('status', 'N/A'),
                  'date': track_status.get('datetime', 'N/A'),
                  'location': track_status.get('location', 'N/A')
              }
              for track_status in all_track_status
          ]

          delivery = {
              'estimateDelivery': estimatedDate,
              'status': eventStatus
          }

        except (KeyError, IndexError, TypeError) as e:
          print("Error processing tracking data:", str(e))
          delivery = {
              'estimateDelivery': None,
              'status': [],
              'error': 'Tracking information is incomplete or unavailable.'
          }
        return delivery
    

    def postAfterShipTracking(self, tracking_number):
        # Try to register tracking number if not found
        headers = {
            "aftership-api-key": self.aftershipApiKey,
            "Content-Type": "application/json"
        }
        register_data = {
            "tracking": {
                "tracking_number": tracking_number,
                "carrier": "USPS"
            }
        }
        response = requests.post(self.aftershipUrl, headers=headers, json=register_data)
        print(response.status_code)
        return True
