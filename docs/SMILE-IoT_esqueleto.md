# SMILE-IoT: Sistema de Monitorização e Inspeção Local de Energia via IoT

**Unidade Curricular:** PESTA (Projeto/Estágio) - LEEC ISEP  
**Autor:** [Teu Nome] ([Teu Número])  
**Data:** Março 2026  
**Estatuto:** Auto-proposta (Trabalhador-Estudante / SWE na Bosch)

---

## 1. Visão Geral (Overview)

O **SMILE-IoT** é um protótipo de sistema embutido para a monitorização não invasiva do consumo de energia elétrica em corrente alternada (AC). O projeto visa responder à necessidade de auditar e perfilar o consumo de equipamentos ou quadros elétricos de forma rápida, segura e económica, sem necessidade de interrupção do circuito ou de intervenções elétricas complexas.

O sistema faz a ponte entre a **Engenharia Eletrotécnica** (aquisição e condicionamento de sinais analógicos, cálculo de potência) e a **Engenharia de Software** (processamento no microcontrolador, transmissão IoT e visualização de dados em tempo real).

## 2. Arquitetura do Sistema

A arquitetura foi desenhada com foco na modularidade e na rápida exequibilidade, dividindo-se em três camadas principais: perceção (Hardware), transporte (Rede) e aplicação (Software).

### Diagrama de Blocos Lógico

```text
[ Rede Elétrica AC ] 
       │
       ▼ (Campo Magnético)
┌────────────────────┐      ┌──────────────────────┐      ┌────────────────────┐
│ 1. Sensor SCT-013  ├─────►│ 2. Condicionamento   ├─────►│ 3. Microcontrolador│
│ (Transformador de  │      │ (Divisor de Tensão + │      │ ESP32 (ADC 12-bit) │
│  Corrente 30A/1V)  │      │  Filtro DC Offset)   │      │ Processamento RMS  │
└────────────────────┘      └──────────────────────┘      └─────────┬──────────┘
                                                                    │
                                                                    ▼ (Wi-Fi / MQTT)
┌────────────────────┐      ┌──────────────────────┐      ┌────────────────────┐
│ 6. Utilizador Final│◄─────┤ 5. Dashboard Web     │◄─────┤ 4. Servidor IoT    │
│ (Browser/Mobile)   │      │ (Gráficos Tempo Real)│      │ (Broker/Backend)   │
└────────────────────┘      └──────────────────────┘      └────────────────────┘
