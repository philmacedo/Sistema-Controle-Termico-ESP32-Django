#include<WiFi.h>
#include <HTTPClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <ArduinoJson.h>

const char* ssid = "Wokwi-GUEST";
const char* pass = "";
unsigned const long interval = 10000;
unsigned long zero = 0;

int DS_PIN = 13;
OneWire oneWire(DS_PIN);
DallasTemperature sensors(&oneWire);

String servidor = "https://philipy.pythonanywhere.com";
String deviceID = "ESP32_01";

//pinos
int PIN_FAN = 5; //led azul (ventoinha)
int PIN_RELAY = 26; //relé
int PIN_LED_OK = 19; //LED Verde
int PIN_LED_ERR = 18; //LED Vermelho
int PIN_TURBO = 12; //Botão azul (modo turbo)
int PIN_VIBRA = 27; //Botão verde (vibração)
int PIN_DOOR = 14; //Slide switch (porta)

//variáveis e objetos
float temperature = 25.0;
float setpoint = 40.0;
bool remoteCutoff = false; //botão emergencia via Django
int dutyCycle = 0;
bool relayState = true;

float maxOvershoot = 20.0; //config. overshoot de segurança

float Kp = 2.0; // Proporcional
float Ki = 0.8; // Integral
float Kd = 5.0; // Derivativo

float erroAnterior = 0.0;
float somaErro = 0.0;

int statusDoor = 0;
bool vibraAtivo = false;
bool turboAtivo = false;

int lastTurboState = HIGH;
int lastVibraState = HIGH;

// Timer para Controle Local (PID)
unsigned long lastControlTime = 0;
const long controlInterval = 1000; //1s

void setup() {
  Serial.begin(115200);
  
  pinMode(PIN_FAN, OUTPUT);
  pinMode(PIN_RELAY, OUTPUT);
  pinMode(PIN_LED_OK, OUTPUT);
  pinMode(PIN_LED_ERR, OUTPUT);

  pinMode(PIN_TURBO, INPUT_PULLUP);
  pinMode(PIN_VIBRA, INPUT_PULLUP);
  pinMode(PIN_DOOR, INPUT);

  sensors.begin();

  Serial.println("Sistema Inicializando....");
  WiFi.begin(ssid, pass, 6);
  while(WiFi.status() != WL_CONNECTED){
    delay(100);
    Serial.println(".");
  }
  Serial.println("WiFi Connected!");
  Serial.println(WiFi.localIP());

  digitalWrite(PIN_RELAY, HIGH); // Estado inicial: Sistema Ligado

}

void loop() {
  unsigned long currentMillis = millis();

  //Loop controle
  if (currentMillis - lastControlTime >= controlInterval){
    lastControlTime = currentMillis;

    //simulação física
    sensors.requestTemperatures();
    float calorEntrada = sensors.getTempCByIndex(0);

    // Capacidade máxima de resfriamento: 20 graus
    float resfriamento = (dutyCycle / 100.0) * 20.0;

    //Física simulada
    float deltaT = (calorEntrada - resfriamento) - temperature;
    temperature = temperature + (deltaT * 0.1); // 0.1 é a inércia térmica (simula a massa do dissipador)

    //leitura digital
    int leituraTurbo = digitalRead(PIN_TURBO);
    if (lastTurboState == HIGH && leituraTurbo == LOW){
      turboAtivo = !turboAtivo;
      Serial.print("Modo Turbo: ");
      Serial.println(turboAtivo ? "LIGADO" : "DESLIGADO");
    }
    lastTurboState = leituraTurbo;

    int leituraVibra = digitalRead(PIN_VIBRA);
    if (lastVibraState == HIGH && leituraVibra == LOW){
      vibraAtivo = !vibraAtivo;
      Serial.print("Simulação de Vibração: ");
      Serial.println(vibraAtivo ? "ATIVADA" : "DESATIVADA");
    }
    lastVibraState = leituraVibra;

    statusDoor = digitalRead(PIN_DOOR);

    //lógica de segurança (local + remota)
    bool isEmergency = false;

    //verifica condições de risco
    if (temperature > 80.0 || 
        temperature > (setpoint + maxOvershoot) ||
        statusDoor == HIGH ||
        vibraAtivo == true ||
        remoteCutoff == true){
      isEmergency = true;
    }

    if (isEmergency){
      digitalWrite(PIN_RELAY, LOW); //corta energia
      digitalWrite(PIN_LED_ERR, HIGH);
      digitalWrite(PIN_LED_OK, LOW);
      dutyCycle = 100; //ventoinha no máx
      relayState = false;

      // Log no Serial
      if(remoteCutoff) Serial.println("[ALERTA] Corte Remoto via Django Ativo!");
      else if(vibraAtivo) Serial.println("[ALERTA] Vibração Detectada!");
      else if(statusDoor) Serial.println("[ALERTA] Porta Aberta!");
      else Serial.println("[ALERTA] Superaquecimento!");

    } else {
      //operação normal
      digitalWrite(PIN_RELAY, HIGH);
      digitalWrite(PIN_LED_ERR, LOW);
      digitalWrite(PIN_LED_OK, HIGH);
      relayState = true;

      //controle manual ou proporcional
      if (turboAtivo == true){
        dutyCycle = 100; // Turbo manual ignora PID
        somaErro = 0; // Reseta integral
      } else {
        float erro = temperature - setpoint;

        //termo integral
        if (erro < 0){
          somaErro = somaErro * 0.9; // Reduz 10% da soma a cada ciclo
        }
        else if (erro < 50){
          somaErro = somaErro + erro;
        }


        // Calcula a Derivada
        float derivada = erro - erroAnterior;

        // Fórmula PID
        float saidaPID = (Kp * erro) + (Ki * somaErro) + (Kd * derivada);

        // Converte para Duty Cycle (0 a 100%)
        if (saidaPID > 100) saidaPID = 100;
        if (saidaPID < 0) saidaPID = 0;

        dutyCycle = (int)saidaPID;

        erroAnterior = erro; // Guarda o erro atual
        
      }
    }

    // Aplica PWM na Ventoinha
    int pwmValue = map(dutyCycle, 0, 100, 0, 255);
    analogWrite(PIN_FAN, pwmValue);

    Serial.printf("T:%.2f | SP:%.2f | Fan:%d%% | Vibra:%d | Turbo:%d\n | Remoto:%d\n", temperature, setpoint, dutyCycle, vibraAtivo, turboAtivo, remoteCutoff);
    
  }

  //conectar com a rede
  if (currentMillis - zero >= interval){
    zero = currentMillis;

    if(WiFi.status() == WL_CONNECTED){
      HTTPClient http;

      String url = servidor + "/gravar/" + deviceID + "/" +
                   String(temperature) + "/" + String(dutyCycle) + "/" +
                   String(relayState) + "/" + String(statusDoor) + "/" +
                   String(vibraAtivo) + "/";

      http.begin(url);
      int httpCode = http.GET();

      if (httpCode > 0){
          String payload = http.getString();
          StaticJsonDocument<200> doc;
          if(!deserializeJson(doc, payload)){
              float sp = doc["setpoint"];
              if (sp > 0) setpoint = sp;
              remoteCutoff = doc["remote_cutoff"];
              Serial.println("Dados enviados e Config atualizada.");
         }
      }
      http.end();
    }

  }

}
