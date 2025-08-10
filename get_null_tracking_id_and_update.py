
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "valley_hatchery_tracking.settings")  # Change to your settings path
django.setup()


from tracking_api.models import Tracking
from tracking_api.trackingProduct import TrackAPI

tracking_list = Tracking.objects.filter(tracking_id__isnull=True)
tracking_info = []

for tracking in tracking_list:
    print("Tracking Number in Model:", tracking.tracking_number)
    tracking_info.append({
        "tracking_number": tracking.tracking_number,
        'order_number': tracking.order_number,
    })
    tracking.delete()
    print("Deleted tracking Number Successfully.")
print("Tracking Info:", tracking_info)

for tracking in tracking_info:
    tracking_number = tracking['tracking_number']
    order_number = tracking['order_number']
    print("Tracking Number:", tracking_number)
    print("Order Number:", order_number)
    track_api = TrackAPI()
    # tracking_id = track_api.postAfterShipTracking(data['tracking_number'])
    tracking_id = track_api.postAfterShipTrackingVersion2(tracking_number=tracking_number)
    if tracking_id is False:
        print(f"Failed to create tracking ID for {tracking_number}")
        continue
    
    
    # Create a new Tracking object with the tracking number and order number
    new_tracking = Tracking.objects.create(
        tracking_id=tracking_id,
        tracking_number=tracking_number,
        order_number=order_number
    )
    print(f"Created new tracking with ID: {new_tracking.tracking_id}")


print("All tracking IDs updated successfully.", len(tracking_info), "records processed.")