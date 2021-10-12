# OCU diagram

```mermaid
graph LR
   subgraph Organic Coating Unit
         subgraph Preconditioning
                  rH[Humidifier]
                  Bypass
                  Inlet
                  end
         subgraph Outlets
                  FO[Main]
                  PO[Flow Dump]
                  end
         subgraph First Dosing Stage
                  MFC1
                  Mixing --> PID1
                  VOC1 -->|Heated Line| Mixing
                  PID1 --> f1[Flow Regulator]
                  end
         subgraph Second Dosing Stage
                  MFC2
                  M2[Mixing] --> PID2
                  VOC2 --> M2
                  PID2 --> f2[Flow Regulator]
                  end
         rH ==> Inlet
         Bypass ==> Inlet
         Inlet ==> Mixing
         MFC1 --> |0 to 0.1 lpm| VOC1
         VOC1 -.-|Control Loop| PID1
         Mixing ==> M2
         MFC2 --> |0 to 0.1 lpm| VOC2
         f1 --> |0 to 0.5 lpm| PO
         f2 --> |0 to 0.5 lpm| PO
         M2 ==> OFR[Oxidation Flow Reactor]
         OFR ==> FO
   end
D((Synth. Air)) --> MFC1
D --> MFC2
A[Synth. Air / Seed Aerosol] ==> rH 
A ==> Bypass
FO ==> E[SOM Aerosol]
linkStyle 10 stroke:blue,stroke-width:2px,curve:natural,stroke-dasharray: 8 8;
linkStyle 1 stroke:red,stroke-width:2px,curve:natural;
```

## Generation of Pure Secondary Organic Matter Particles by Homogeneous Nucleation

```mermaid
graph LR
subgraph OCU
         Inlet[Inlet] --> Mixing
         Mixing --> OFR
         VOC1 --> Mixing
         Mixing --> PID
         VOC1 -.-|Control Loop| PID
         end
A((Air)) --> B[Flow Controller] 
B  --> |2 lpm| Inlet
D((N<sub>2</sub>)) --> |2 Bar| VOC1
OFR --> |1 lpm - SOA| E[Characterization]
PID -.1 lpm - Filtered.-> F((Flow Dump))
linkStyle 4 stroke:blue,stroke-width:2px,curve:natural,stroke-dasharray: 8 8;
```

```mermaid
graph LR
subgraph Organic Coating Unit
         subgraph in
                  Inlet[Inlet]
                  VOC1
                  VOC2
                  end
         subgraph out
                  FO[Front Outlet]
                  PO[Pump Outlet]
                  end
         Inlet --> Mixing
         VOC1 --> Mixing
         VOC2 --> M2[Mixing]
         Mixing --> PID1
         VOC1 -.-|Control Loop| PID1
         Mixing --> M2
         M2 --> PID2
         PID1 --> |0.5 lpm| PO
         PID2 --> |0.5 lpm| PO
         M2 --> OFR
         OFR --> FO
         end
A((Air)) --> B[Flow Controller] 
B  --> |2 lpm| Inlet
D((N<sub>2</sub>)) --> |2 Bar| VOC1
FO --> |1 lpm - SOA| E[Characterization]
PO -.1 lpm - Filtered.-> F((Flow Dump))
linkStyle 4 stroke:blue,stroke-width:2px,curve:natural,stroke-dasharray: 8 8;
```

```mermaid
graph LR
   subgraph Organic Coating Unit
         subgraph in
                  Inlet[Inlet]
                  MFC1
                  MFC2
                  end
         subgraph out
                  FO[Front Outlet]
                  PO[Pump Outlet]
                  end
         subgraph VOC1 Mixing
                  Mixing --> PID1
                  VOC1 -->|VOC Heater| Mixing
                  end
         subgraph VOC2 Mixing
                  M2[Mixing] --> PID2
                  VOC2 --> M2
                  end
         Inlet ==> Mixing
         MFC1 --> VOC1
         VOC1 -.-|Control Loop| PID1
         Mixing ==> M2
         MFC2 --> VOC2
         PID1 --> |0.5 lpm| PO
         PID2 --> |0.5 lpm| PO
         M2 ==> OFR
         OFR ==> FO
   end
D((N<sub>2</sub>)) --> |2 Bar| MFC1
A((Air)) ==> B[Flow Controller] 
B  ==> |2 lpm| Inlet
FO ==> |1 lpm - SOA| E[Characterization]
PO -.1 lpm - Filtered.-> F((Flow Dump))
linkStyle 6 stroke:blue,stroke-width:2px,curve:natural,stroke-dasharray: 8 8;
linkStyle 1 stroke:red,stroke-width:2px,curve:natural;
```



## Coating of Particles with Secondary Organic Matter

```mermaid
graph LR
subgraph OCU
         Inlet[Inlet] --> Mixing
         Mixing --> OFR
         VOC1 --> Mixing
         Mixing --> PID
         VOC1 -.-|Control Loop| PID
         end
A[MiniCAST] ==> |2 lpm| Inlet
D((N<sub>2</sub>)) --> |2 Bar| VOC1
OFR --> |1 lpm - Coated Soot| E[Characterization]
PID -.1 lpm - Filtered.-> F((Flow Dump))
linkStyle 4 stroke:blue,stroke-width:2px,curve:natural,stroke-dasharray: 8 8;
```

```mermaid
graph LR
subgraph Organic Coating Unit
         subgraph in
                  Inlet[Inlet]
                  VOC1
                  VOC2
                  end
         subgraph out
                  FO[Front Outlet]
                  PO[Pump Outlet]
                  end
         Inlet --> Mixing
         VOC1 --> Mixing
         VOC2 --> M2[Mixing]
         Mixing --> PID1
         VOC1 -.-|Control Loop| PID1
         Mixing --> M2
         M2 --> PID2
         PID1 --> |0.5 lpm| PO
         PID2 --> |0.5 lpm| PO
         M2 --> OFR
         OFR --> FO
         end
B[MiniCAST] 
B  --> |2 lpm| Inlet
D((N<sub>2</sub>)) --> |2 Bar| VOC1
FO --> |1 lpm - Coated Soot| E[Characterization]
PO -.1 lpm - Filtered.-> F((Flow Dump))
linkStyle 4 stroke:blue,stroke-width:2px,curve:natural,stroke-dasharray: 8 8;
```

```mermaid
graph LR
   subgraph Organic Coating Unit
         subgraph in
                  Inlet[Inlet]
                  MFC1
                  MFC2
                  end
         subgraph out
                  FO[Front Outlet]
                  PO[Pump Outlet]
                  end
         subgraph VOC1 Mixing
                  Mixing --> PID1
                  VOC1 -->|VOC Heater| Mixing
                  end
         subgraph VOC2 Mixing
                  M2[Mixing] --> PID2
                  VOC2 --> M2
                  end
         Inlet ==> Mixing
         MFC1 --> VOC1
         VOC1 -.-|Control Loop| PID1
         Mixing ==> M2
         MFC2 --> VOC2
         PID1 --> |0.5 lpm| PO
         PID2 --> |0.5 lpm| PO
         M2 ==> OFR
         OFR ==> FO
   end
D((N<sub>2</sub>)) --> |2 Bar| MFC1
B[MiniCAST] ==> |2 lpm| Inlet
FO ==> |1 lpm - Coated Soot| E[Characterization]
PO -.1 lpm - Filtered.-> F((Flow Dump))
linkStyle 6 stroke:blue,stroke-width:2px,curve:natural,stroke-dasharray: 8 8;
linkStyle 1 stroke:red,stroke-width:2px,curve:natural;
```

## Zero point

```mermaid
graph LR
subgraph OCU
         Inlet[Inlet] --> Mixing
         Mixing --> OFR
         VOC1 --> Mixing
         Mixing --> PID
         VOC1 -.-|Control Loop| PID
         end
A((Synth. Air)) --> B[Flow Controller]
B  --> |2 lpm| Inlet
OFR --> |1 lpm | F((Flow Dump))
PID -.1 lpm - Filtered.-> F
linkStyle 4 stroke:blue,stroke-width:2px,curve:natural,stroke-dasharray: 8 8;
```


```mermaid
graph LR
subgraph Organic Coating Unit
         subgraph in
                  Inlet[Inlet]
                  VOC1
                  VOC2
                  end
         subgraph out
                  FO[Front Outlet]
                  PO[Pump Outlet]
                  end
         Inlet --> Mixing
         VOC1 --> Mixing
         VOC2 --> M2[Mixing]
         Mixing --> PID1
         VOC1 -.-|Control Loop| PID1
         Mixing --> M2
         M2 --> PID2
         PID1 --> |0.5 lpm| PO
         PID2 --> |0.5 lpm| PO
         M2 --> OFR
         OFR --> FO
         end
A((Synth. Air)) --> B[Flow Controller]  
B  --> |2 lpm| Inlet
FO --> |1 lpm| F((Flow Dump))
PO -.1 lpm - Filtered.-> F
linkStyle 4 stroke:blue,stroke-width:2px,curve:natural,stroke-dasharray: 8 8;
```

```mermaid
graph LR
   subgraph Organic Coating Unit
         subgraph in
                  Inlet[Inlet]
                  MFC1
                  MFC2
                  end
         subgraph out
                  FO[Front Outlet]
                  PO[Pump Outlet]
                  end
         subgraph VOC1 Mixing
                  Mixing --> PID1
                  VOC1 -->|VOC Heater| Mixing
                  end
         subgraph VOC2 Mixing
                  M2[Mixing] --> PID2
                  VOC2 --> M2
                  end
         Inlet ==> Mixing
         MFC1 --> VOC1
         VOC1 -.-|Control Loop| PID1
         Mixing ==> M2
         MFC2 --> VOC2
         PID1 --> |0.5 lpm| PO
         PID2 --> |0.5 lpm| PO
         M2 ==> OFR
         OFR ==> FO
   end
A((Synth. Air)) ==> B[Flow Controller] 
B  ==> |2 lpm| Inlet
FO ==> |1 lpm| F((Flow Dump))
PO -.1 lpm - Filtered.-> F
linkStyle 6 stroke:blue,stroke-width:2px,curve:natural,stroke-dasharray: 8 8;
linkStyle 1 stroke:red,stroke-width:2px,curve:natural;
```


## Calibration

```mermaid
graph LR
subgraph OCU
         Inlet[Inlet] --> Mixing
         Mixing --> OFR
         VOC1 --> Mixing
         Mixing --> PID
         VOC1 -.-|Control Loop| PID
         end
A((C<sub>4</sub>H<sub>8</sub> mix)) --> B[Flow Controller]
B  --> |2 lpm| Inlet
OFR --> |1 lpm | F((Flow Dump))
PID -.1 lpm - Filtered.-> F
linkStyle 4 stroke:blue,stroke-width:2px,curve:natural,stroke-dasharray: 8 8;
```

```mermaid
graph LR
subgraph Organic Coating Unit
         subgraph in
                  Inlet[Inlet]
                  VOC1
                  VOC2
                  end
         subgraph out
                  FO[Front Outlet]
                  PO[Pump Outlet]
                  end
         Inlet --> Mixing
         VOC1 --> Mixing
         VOC2 --> M2[Mixing]
         Mixing --> PID1
         VOC1 -.-|Control Loop| PID1
         Mixing --> M2
         M2 --> PID2
         PID1 --> |0.5 lpm| PO
         PID2 --> |0.5 lpm| PO
         M2 --> OFR
         OFR --> FO
         end
A((C<sub>4</sub>H<sub>8</sub> mix)) --> B[Flow Controller]  
B  --> |2 lpm| Inlet
FO --> |1 lpm| F((Flow Dump))
PO -.1 lpm - Filtered.-> F
linkStyle 4 stroke:blue,stroke-width:2px,curve:natural,stroke-dasharray: 8 8;
```

```mermaid
graph LR
   subgraph Organic Coating Unit
         subgraph in
                  Inlet[Inlet]
                  MFC1
                  MFC2
                  end
         subgraph out
                  FO[Front Outlet]
                  PO[Pump Outlet]
                  end
         subgraph VOC1 Mixing
                  Mixing --> PID1
                  VOC1 -->|VOC Heater| Mixing
                  end
         subgraph VOC2 Mixing
                  M2[Mixing] --> PID2
                  VOC2 --> M2
                  end
         Inlet ==> Mixing
         MFC1 --> VOC1
         VOC1 -.-|Control Loop| PID1
         Mixing ==> M2
         MFC2 --> VOC2
         PID1 --> |0.5 lpm| PO
         PID2 --> |0.5 lpm| PO
         M2 ==> OFR
         OFR ==> FO
   end
A((C<sub>4</sub>H<sub>8</sub> mix)) ==> B[Flow Controller] 
B  ==> |2 lpm| Inlet
FO ==> |1 lpm| F((Flow Dump))
PO -.1 lpm - Filtered.-> F
linkStyle 6 stroke:blue,stroke-width:2px,curve:natural,stroke-dasharray: 8 8;
linkStyle 1 stroke:red,stroke-width:2px,curve:natural;
```
