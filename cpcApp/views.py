from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import DeviceConfig, Telemetry
from django.utils import timezone

# Create your views here.
def index(request):
    return render(request, 'dashboard.html')

# API para o ESP32
def receber_telemetria(request, device_id, temp, duty, relay, door, vibra):
    try:
        #localizar dispositivo pelo id
        device = DeviceConfig.objects.get(device_id=device_id)

        #atualiza o visto por último para sabermos que está online
        device.last_seen = timezone.now()
        device.save()

        #salva os dados no histórico. Converter inteiro para booleano
        Telemetry.objects.create(
            device=device,
            temperature=float(temp),
            duty_cycle=int(duty),
            relay_active=bool(int(relay)),
            door_open=bool(int(door)),
            vibration_detected=bool(int(vibra))
        )

        #resposta
        data = {
            "mensagem": "Dados Recebidos",
            "setpoint": device.setpoint,
            "remote_cutoff": device.remote_cutoff,
        }
        return JsonResponse(data, status=200)

    except DeviceConfig.DoesNotExist:
        return JsonResponse({"erro": "Dispositivo não cadastrado!"}, status=404)
    except Exception as e:
        return JsonResponse({"erro": str(e)}, status=500)

# API para o dashboard
def dados_dashboard(request, device_id):
    try:
        device = DeviceConfig.objects.get(device_id=device_id)

        #PEGA última leitura registrada
        ultima_leitura = device.telemetries.first() #lembrando que foi ordenado -timestamp no models

        if ultima_leitura:
            dados={
                "device_name": device.name,
                "setpoint": device.setpoint,
                "remote_cutoff": device.remote_cutoff,
                "last_seen": device.last_seen,
                "temperatura": ultima_leitura.temperature,
                "duty_cycle": ultima_leitura.duty_cycle,
                "relay": ultima_leitura.relay_active,
                "alerta_porta":  ultima_leitura.door_open,
                "alerta_vibra": ultima_leitura.vibration_detected,
                "horario": ultima_leitura.timestamp.strftime("%H:%M:%S")
            }

        else:
            dados = {"mensagem": "Sem Dados Ainda"}

        return JsonResponse(dados, status=200)

    except DeviceConfig.DoesNotExist:
        return JsonResponse({"erro": "Dispositivo não cadastrado!"}, status=404)

# API para alterar setpoint
def definir_setpoint(request, device_id, novo_setpoint):
    try:
        device = DeviceConfig.objects.get(device_id=device_id)

        #atualiza setpoint
        device.setpoint = float(novo_setpoint)
        device.save()

        return JsonResponse({
            "mensagem": "Setpoint ATUALIZADO com Sucesso!",
            "novo_setpoint": device.setpoint
        }, status=200)

    except DeviceConfig.DoesNotExist:
        return JsonResponse({"erro": "Dispositivo não cadastrado!"}, status=404)

# botao no dashboard de emergencia
def alternar_emergencia(request, device_id):
    try:
        device = DeviceConfig.objects.get(device_id=device_id)
        # Inverte o estado (Se tava True vira False, e vice-versa)
        device.remote_cutoff = not device.remote_cutoff
        device.save()

        status_str = "ATIVADO" if device.remote_cutoff else "DESATIVADO"
        return JsonResponse({"mensagem": f"Corte remoto {status_str}!", "estado": device.remote_cutoff})
    except DeviceConfig.DoesNotExist:
        return JsonResponse({"erro": "Device não encontrado"}, status=404)

