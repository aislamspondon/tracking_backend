import json
import requests
import http.client
import random

class TrackAPI:
    # Ship24 config
    ship24Url = "https://api.ship24.com/public/v1/trackers"
    ship24ApiKey = "apik_CjnUCgyp4aJBRYbArHGb3kCYeBvYhI"

    # AfterShip config
    aftershipUrl = "https://api.aftership.com/v4/trackings"
    aftershipPrimaryUrl = "api.aftership.com"
    aftershipApiKey = "asat_13c8b5487df24312b1fa3efe20da5171"


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
            # print("Tracking Status Object:", status)
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
        print("----------------------------------------------------------")
        print("Tracking Status Object:------------>")
        print(json.dumps(tracking, indent=4))
        print("----------------------------------------------------------")

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
        #   print("Tracking Status Object:", status)
          all_track_status = status.get('events', [])
          estimatedDate = status.get('shipment', {}).get('delivery', {}).get('estimatedDeliveryDate', None)

          eventStatus = [
              {
                  'status': track_status.get('status', []),
                  'date': track_status.get('datetime', None),
                  'location': track_status.get('location', None)
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
    

    def AfterShipTrackingVersion2(self, tracking_id):
        conn = http.client.HTTPSConnection(self.aftershipPrimaryUrl)
        headers = {
            "Content-Type": "application/json",
            "as-api-key": self.aftershipApiKey
        }
        endpoint = f"/tracking/2025-07/trackings/{tracking_id}"
        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()
        data = res.read()
        if res.status != 200:
            return {"error": "Tracking number not found."}
        raw_data = json.loads(data.decode("utf-8"))
        tracking = raw_data.get("data", {})
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
                                "originCountryCode": tracking.get("origin_country_region"),
                                "destinationCountryCode": tracking.get("destination_country_region"),
                                "delivery": {
                                    "estimatedDeliveryDate": tracking.get("custom_estimated_delivery_date")
                                },
                            },
                            "events": tracking.get("checkpoints", [])
                        }
                    ]
                }
            }
        # print("Tracking Status Object:------------>", json.dumps(formatted_output, indent=4))
        status = formatted_output['data']['trackings'][0]
        try:
            status = formatted_output['data']['trackings'][0]
            for event in status['events']:
                event['status'] = event.pop('message')
                event['datetime'] = event.pop('checkpoint_time')
            # print("Tracking Status Object:", status)
            all_track_status = status.get('events', [])
            estimatedDate = status.get('shipment', {}).get('delivery', {}).get('estimatedDeliveryDate', None)
            eventStatus = [
                {
                    'status': track_status.get('status', []),
                    'date': track_status.get('datetime', None),
                    'location': track_status.get('location', None)
                }
                for track_status in all_track_status
            ]
            # print("eventStatus:", eventStatus)
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
    
    def postAfterShipTrackingVersion2(self, tracking_number):
        url = "https://api.aftership.com/tracking/2025-07/trackings"

        headers = {
        "Content-Type": "application/json",
            "as-api-key": self.aftershipApiKey
        }
        tracking_data = {
            "tracking_number": tracking_number
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(tracking_data))
            response.raise_for_status()  # Raise exception for HTTP errors
            print("Tracking created successfully:")
            tracking_id =  response.json().get("data",{}).get("id", False)
            return tracking_id
        except Exception as e:
            print(f"Error creating tracking: {e}")
            return False
        