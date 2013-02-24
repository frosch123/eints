from datetime import datetime

def get_datetime_now_formatted():
    # useful for user messages when creating or updating objects
    return datetime.now().strftime('%c')

def get_messages(request):
    # message classes map to bootstrap css alert style names. n.b. default bootstrap alert is yellow (warning), but our default is blue (info)
    message_classes = {'info': 'alert-info', 'warning':'', 'success': 'alert-success', 'error': 'alert-error'}

    messages = []
    if len(request.query.get('message', '')) > 0:
        message = {}
        message['content'] = request.query.get('message', '')
        message['class'] = message_classes[request.query.get('message_class', 'info')]
        messages.append(message)

    if len(messages) > 0:
        return messages
    else:
        return None