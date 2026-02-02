from utils.dataloader import clear_drive_files

ALL_LOGS_drive, CHAT_HISTORY_drive = "1eTJ0qRUJNLrlHkS9uZkc5UbTr5Ax5vxQ", "1ojmP_z1W1Q41velLHAjmhL1XmN-Sz7xt"
BUTTON_HISTORY_drive = '1GU9Wg2bDDt2zhjqZNodwKr4oZeK-5_RB'
LOG_SLIDER_CHANGES_PERMANENT_drive = '1jjcXv9vuy07ED1NSjJsdgP4NrgYk0bru'
LOG_SUBMISSION_DRIVE = '1g8LWArYUFgTE0Js4DgUM9ei9gMvA5vDG'

LIST = [ALL_LOGS_drive, CHAT_HISTORY_drive, BUTTON_HISTORY_drive, 
LOG_SLIDER_CHANGES_PERMANENT_drive, LOG_SUBMISSION_DRIVE]

for i in range(len(LIST)):
    clear_drive_files(LIST[i])
print("Done")