from django.db import models
from django.utils import timezone

# modelo para armazenar a configuração atual do ESP32
class DeviceConfig(models.Model):
    device_id = models.CharField(max_length=50, unique=True, default="ESP32_01", verbose_name="ID do Dispositivo")
    name = models.CharField(max_length=100, default="Servidor Principal", verbose_name="Nome Amigável")

    # Este é o SETPOINT que o ESP32 vai baixar
    setpoint = models.FloatField(default=40.0, verbose_name="Setpoint (°C)")

    #segurança
    remote_cutoff = models.BooleanField(default=False, verbose_name="Corte de Emergência Remoto")

    # Para saber se o dispositivo está online (data da última comunicação)
    last_seen = models.DateTimeField(default=timezone.now, verbose_name="Último Visto")


    def __str__(self):
        return f"{self.name} ({self.device_id}) - SP: {self.setpoint}°C"

    class Meta:
        verbose_name = "Configuração do Dispositivo"
        verbose_name_plural = "Configurações dos Dispositivos"

#Armazena o histórico de leituras enviadas pelo ESP32
class Telemetry(models.Model):

    device = models.ForeignKey(DeviceConfig, on_delete=models.CASCADE, related_name='telemetries')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Data/Hora")

    # Dados Analógicos
    temperature = models.FloatField(verbose_name="Temperatura Real (°C)")
    duty_cycle = models.IntegerField(verbose_name="Velocidade Ventoinha (%)")

    # Dados Digitais de Segurança (Status)
    relay_active = models.BooleanField(default=False, verbose_name="Relé Ativado?")
    door_open = models.BooleanField(default=False, verbose_name="Porta Aberta?")
    vibration_detected = models.BooleanField(default=False, verbose_name="Vibração?")

    def __str__(self):
        return f"{self.timestamp.strftime('%H:%M:%S')} - Temp: {self.temperature}°C"

    class Meta:
        verbose_name = "Telemetria"
        verbose_name_plural = "Histórico de Telemetria"
        ordering = ['-timestamp'] # Mostra os mais recentes primeiro

