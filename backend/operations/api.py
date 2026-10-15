"""Staff-only JSON API. Basic credentials require HTTPS outside localhost."""
import base64
import csv
import json
from functools import wraps
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware
from .models import WorkOrder, Activity

NEXT = {'queued': 'preparing', 'preparing': 'ready', 'ready': 'closed'}

def staff_only(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        try:
            scheme, token = request.headers.get('Authorization', '').split(' ', 1)
            if scheme.lower() != 'basic': raise ValueError()
            username, password = base64.b64decode(token, validate=True).decode().split(':', 1)
            user = authenticate(username=username, password=password)
        except (ValueError, UnicodeError):
            user = None
        if not user or not user.is_active or not user.is_staff:
            response = JsonResponse({'error': 'Valid staff credentials required.'}, status=401)
            response['WWW-Authenticate'] = 'Basic realm="MiseOps"'
            return response
        request.actor = user.username
        return view(request, *args, **kwargs)
    return wrapped

def serialize(order):
    return {'id': order.pk, 'title': order.title, 'station': order.station, 'assignee': order.assignee,
            'quantity': order.quantity, 'due': order.due.isoformat(), 'priority': order.priority,
            'status': order.status, 'notes': order.notes,
            'activity': list(order.activity.values('actor', 'message', 'created_at'))}

def filtered(request):
    records = WorkOrder.objects.prefetch_related('activity')
    if request.GET.get('q'): records = records.filter(title__icontains=request.GET['q'])
    if request.GET.get('status'): records = records.filter(status=request.GET['status'])
    return records

@staff_only
def orders(request):
    if request.method == 'GET': return JsonResponse({'orders': [serialize(x) for x in filtered(request)]})
    if request.method != 'POST': return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict): raise ValueError('Expected a JSON object')
        due = parse_datetime(str(data.get('due', '')))
        if due is None or not is_aware(due): raise ValueError('Due date needs a timezone')
        quantity = data.get('quantity')
        if type(quantity) is not int or quantity < 1: raise ValueError('Quantity must be a positive integer')
        order = WorkOrder(due=due, quantity=quantity)
        for field in ('title', 'station', 'assignee', 'notes', 'priority'):
            if field in data:
                if not isinstance(data[field], str): raise ValueError('Fields must contain text')
                setattr(order, field, data[field].strip())
        order.full_clean()
        with transaction.atomic():
            order.save()
            Activity.objects.create(order=order, actor=request.actor, message='Work order created')
        return JsonResponse(serialize(order), status=201)
    except (ValueError, TypeError, ValidationError) as error:
        return JsonResponse({'error': str(error)}, status=400)

@staff_only
def transition(request, pk):
    if request.method != 'POST': return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict): raise ValueError()
    except (ValueError, TypeError): return JsonResponse({'error': 'Expected a JSON object'}, status=400)
    with transaction.atomic():
        order = WorkOrder.objects.select_for_update().filter(pk=pk).first()
        if order is None: return JsonResponse({'error': 'Work order not found'}, status=404)
        if data.get('status') != NEXT.get(order.status) or order.status == 'closed':
            return JsonResponse({'error': 'Invalid workflow transition'}, status=409)
        order.status = data['status']
        order.save()
        Activity.objects.create(order=order, actor=request.actor, message=f'Moved to {order.status}')
    return JsonResponse(serialize(order))

@staff_only
def export(request):
    if request.method != 'GET': return JsonResponse({'error': 'Method not allowed'}, status=405)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="miseops-work-orders.csv"'
    writer = csv.writer(response)
    writer.writerow(['id', 'title', 'station', 'assignee', 'quantity', 'due', 'status'])
    for order in filtered(request):
        row = [order.pk, order.title, order.station, order.assignee, order.quantity, order.due.isoformat(), order.status]
        writer.writerow(["'" + str(v) if str(v).lstrip().startswith(('=', '+', '-', '@')) else v for v in row])
    return response
