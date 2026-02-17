import json
import requests
import http.client
from dateutil import parser

def convert_timezone(timestamp_str):
    """
    Convert ISO8601 timestamp string with timezone info to another timezone.

    Args:
        timestamp_str (str): Original timestamp string, e.g. '2025-08-03T16:28:00-05:00'
        target_timezone_str (str): Target timezone name, e.g. 'America/New_York'

    Returns:
        str: Converted timestamp string in format 'YYYY-MM-DDTHH:MM:SS±HHMM'
    """
    # Parse original timestamp string (aware datetime)
    dt = parser.parse(timestamp_str)
    
    print(dt, "Parsed datetime object")
    formatted = dt.strftime("%b %d, %Y at %I:%M %p")
    print(formatted)  # Output: Aug 06, 2025 at 08:13 AM
    return formatted


class TrackAPI:
    # Ship24 config
    
    ship24Url = "https://api.ship24.com/public/v1/trackers"
    ship24ApiKey = "apik_HGp31VBDpsrQsGV8wD1xO0ZbuljObz"

    # AfterShip config
    aftershipUrl = "https://api.aftership.com/v4/trackings"
    aftershipPrimaryUrl = "api.aftership.com"
    aftershipApiKey = "asat_13c8b5487df24312b1fa3efe20da5171"
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c3BzX3RyYWNraW5nX3VzZXIiLCJleHAiOjE3NTcyODYxMzB9.tKsDMPIBU3uL-0ll9-G-e9AfcEUB1eqt8R7f_XWuR4M"


    def get_access_token(self):
        url = "https://usps.vhtracking.com/api/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "username": "usps_tracking_user",
            "password": "USDKpaw3C3Rc"
        }
        try:
            response = requests.post(url, data=data, headers=headers)

            if response.status_code == 200:
                print("Token retrieved successfully.")
                print(response.json(), "Response JSON")
                token = response.json().get("access")
                self.token = token  # Store the token for future use
                return True
            else:
                print(f"Failed to retrieve token. Status code: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return False

    



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
            
            trackerUrl = f"https://api.ship24.com/public/v1/trackers/search/{trackingNumber}/results"
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
            print(f"Error fetching tracking information: {e}")
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
        print(delivery, "Delivery Object")
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
                    'date': convert_timezone(track_status.get('datetime', None)),
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
        payload = {
            "tracking_number": tracking_number
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response_data = response.json()
            print("Tracking created successfully:")
            print(response_data, "Response Data")
            tracking_id =  response_data.get("data", {}).get("id", False)
            return tracking_id
        except Exception as e:
            print(f"Error creating tracking: {e}")
            return False
        

    def trackusps(self, tracking_number):
        # First, try to post the tracking number to AfterShip
        print("USPS Script Track Function ---->")
        url = "https://usps.vhtracking.com/info/"
        payload = {
            "tracking_number": tracking_number
        }
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        print(tracking_number, "Tracking Number to be sent")

        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 401:
                print("Unauthorized: Check your API token.")
                response_data = self.get_access_token()
                if response_data:
                    print("Token refreshed. Retrying...")
                    headers["Authorization"] = f"Bearer {self.token}"
                    response = requests.post(url, json=payload, headers=headers)
                else:
                    print("Failed to refresh token.")
        except Exception as e:
            print(f"Error posting tracking number: {e}")

        # Print status code and JSON response
        tracking_status = response.json()['result']
        print("Status Code:", response.status_code)
        try:
            return tracking_status
        except Exception as e:
            print(response.text)
            print(f"Error parsing response: {e}")


    def ship24Tracking(self, tracking_number):
        headers = {
            "Authorization": f"Bearer {self.ship24ApiKey}",
            "Content-Type": "application/json; charset=utf-8"
        }
        payload = {"trackingNumber": tracking_number}
        try:
            response = requests.post(self.ship24Url, headers=headers, data=json.dumps(payload))
        except Exception as e:
            print("------------------------------------Error fetching tracking information------------------------------------")
            print(f"Error fetching tracking information: {e}")

        url = f"https://api.ship24.com/public/v1/trackers/search/{tracking_number}/results"

        headers = {
            "Authorization": f"Bearer {self.ship24ApiKey}",
            "Accept": "application/json"
        }
        try:
            response = requests.get(url, headers=headers)
        except Exception as e:
            print("------------------------------------Error fetching tracking information------------------------------------")
            print(f"Error fetching tracking information: {e}")
        if not response.ok:
            return {
                "error": "Ship24 error",
                "status": response.status_code,
                "body": response.text
            }
        print("---------------------------------------------------------------Response from Ship24 API---------------------------------------------------------------")
        response_json = response.json()
        status = response_json['data']['trackings'][0]
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
        print(delivery, "Delivery Object")
        return delivery