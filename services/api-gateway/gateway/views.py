"""
API Gateway — proxy transparent vers auth-service et core-service.
Toutes les requêtes du frontend passent par le port 8000.
"""
import requests
from django.conf import settings
from django.http import JsonResponse, HttpResponse


def _proxy(request, service_url: str, path: str) -> HttpResponse:
    url = f"{service_url}/{path}"
    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in ('host', 'content-length')}

    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=request.body if request.method not in ('GET', 'HEAD') else None,
            params=request.GET,
            timeout=30,
            allow_redirects=False,
            stream=True,
        )
    except requests.ConnectionError:
        return JsonResponse({'error': f'Service indisponible : {service_url}'}, status=503)
    except requests.Timeout:
        return JsonResponse({'error': 'Timeout du service.'}, status=504)

    # Réponse binaire (PDF, CSV)
    content_type = resp.headers.get('Content-Type', '')
    if 'application/pdf' in content_type or 'text/csv' in content_type:
        response = HttpResponse(resp.content, content_type=content_type, status=resp.status_code)
        if 'Content-Disposition' in resp.headers:
            response['Content-Disposition'] = resp.headers['Content-Disposition']
        return response

    return HttpResponse(
        content=resp.content,
        status=resp.status_code,
        content_type=content_type,
    )


def proxy_auth(request, path=''):
    return _proxy(request, settings.AUTH_SERVICE_URL, f'api/auth/{path}')


def proxy_core(request, path=''):
    return _proxy(request, settings.CORE_SERVICE_URL, f'api/{path}')
