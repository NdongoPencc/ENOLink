"""
CGA-Service views — reçoit les données du core-service, exécute le CGA,
renvoie les résultats au core-service via son API interne.
"""
import threading
import uuid
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .cga import CGA

# Stockage en mémoire des jobs en cours (suffisant pour le prototype)
_jobs: dict[str, dict] = {}


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def lancer_cga_view(request):
    """
    Reçoit les paramètres + données du core-service et lance le CGA.
    Body JSON attendu :
    {
        "regroupement_id": int,
        "apprenants": [...],
        "enos": {...},
        "w1": float, "w2": float,
        "taille_min": int, "taille_max": int,
        "nb_generations": int, "taille_population": int, "seed": int,
        "callback_url": "http://localhost:8002/api/regroupements/{id}/resultats/"
    }
    """
    data = request.data
    job_id = str(uuid.uuid4())

    _jobs[job_id] = {
        'statut': 'EN_COURS',
        'progression': [],
        'resultats': None,
        'erreur': None,
    }

    thread = threading.Thread(
        target=_run_cga,
        args=(job_id, data),
        daemon=True,
    )
    thread.start()

    return Response({'job_id': job_id, 'statut': 'EN_COURS'}, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def statut_cga_view(request, job_id: str):
    """Retourne le statut et la progression d'un job CGA."""
    job = _jobs.get(job_id)
    if not job:
        return Response({'error': 'Job introuvable.'}, status=404)
    return Response(job)


def _run_cga(job_id: str, data: dict):
    import requests as req
    from django.conf import settings

    job = _jobs[job_id]
    try:
        def callback(point):
            job['progression'].append(point)

        cga = CGA(
            apprenants=data['apprenants'],
            enos=data['enos'],
            w1=float(data.get('w1', 0.7)),
            w2=float(data.get('w2', 0.3)),
            taille_min=int(data.get('taille_min', 3)),
            taille_max=int(data.get('taille_max', 6)),
            nb_generations=int(data.get('nb_generations', 200)),
            taille_population=int(data.get('taille_population', 100)),
            seed=int(data.get('seed', 42)),
            callback_progression=callback,
        )
        resultats = cga.executer()
        job['resultats'] = resultats
        job['statut'] = 'TERMINE' if resultats.get('succes') else 'ERREUR'
        job['erreur'] = resultats.get('erreur')

        # Notifier le core-service
        callback_url = data.get('callback_url')
        if callback_url:
            req.post(callback_url, json=resultats, timeout=10)

    except Exception as e:
        job['statut'] = 'ERREUR'
        job['erreur'] = str(e)
