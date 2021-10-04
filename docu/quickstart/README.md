# Organic Coating Unit: Quick Start Manual

# Introduction

# Setting up the OCU for SOM particle production

## Material

1. The organic coating unit
2. Microcomputer
3. VOC containers
5. Sample VOC (e.g. α-pinene)
6. VOC-Free Synthetic air (e.g., Carbagas ALPHAGAZ™ 1 Air)
7. Flow controller capable of delivering 2 lpm (e.g., Mass flow controller, critical orifice, etc.).
8. Innert gas (e.g. N<sub>2</sub>) for VOC dosage and purging the OFR
9. Ultra pure water (e.g. Milli-Q) for humidity experiments
10. 

## The organic coating unit (OCU)

![Front](OCU-QuickStart-0241-screen.jpg)
![Back](OCU-QuickStart-0243-screen.jpg)
![VOC Bottle](OCU-QuickStart-0246-screen.jpg)


## Preparing the OCU for operation

Follow this procedures before the innitial operation.

### 1. Purging the oxidation flow reactor

The coating unit 

![OCU image](OCU-QuickStart-0245-screen.jpg)

## Setup

```mermaid
graph LR
subgraph OCU
         Inlet[Inlet] --> Mixing
         Mixing --> OFR
         VOC1 --> Mixing
         Mixing --> PID
         end
A((Air)) --> B[Flow Controller] 
B  --> |2 lpm| Inlet
D((N<sub>2</sub>)) --> |2 Bar| VOC1
OFR ==> |1 lpm - SOA| E[Characterization]
PID -.1 lpm - Filtered.-> F((Flow Dump))
```

```mermaid
graph LR
subgraph OCU
         Inlet[Inlet] --> Mixing
         Mixing --> OFR
         VOC1 --> Mixing
         Mixing --> PID
         end
A[MiniCAST] ==> |2 lpm| Inlet
D((N<sub>2</sub>)) --> |2 Bar| VOC1
OFR ==> |1 lpm - Coated Soot| E[Characterization]
PID -.1 lpm - Filtered.-> F((Flow Dump))
```



![OCU image](OCU-QuickStart-0236-screen.jpg)

![screenshot](2021-09-17-130618_800x480_scrot.png)
