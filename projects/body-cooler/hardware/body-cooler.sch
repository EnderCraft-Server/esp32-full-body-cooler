EESchema Schematic File Version 4
LIBS:body-cooler-cache
EELAYER 29 0
EELAYER END
$Descr A2 23386 16535
Sheet 1 1
Title "ESP32 全身降温器 接线原理图"
Date "2026-02-14"
Rev "1"
Comp "EnderCraft-Server"
Comment1 "控制端 + 输入端，每处点对点连接都已标注网络名"
Comment2 "低电平触发继电器 / 开漏驱动 / 不含陶瓷与电解电容"
Comment3 ""
Comment4 ""
$EndDescr
Text Notes 700 620 0    90   ~ 0
ESP32 全身降温器 —— 接线原理图（控制端 + 输入端）
Text Notes 700 800 0    55   ~ 0
低电平触发继电器 + 开漏驱动 ／ 不含陶瓷与电解电容 ／ 每一处点对点连接都已标注网络名
Text Notes 700 950 0    55   ~ 0
规则：两个引脚标着同一个网络名，就表示必须手工接的一根线（同名即相连，不必画成实线）。
Text Notes 700 1250 0    75   ~ 0
【一】12V 电源树
$Comp
L body-cooler-cache:BATTERY-3S BT1
U 1 1 5F000001
P 1500 2300
F 0 "BT1" H 1540 2370 50  0000 C CNN
F 1 "3S 锂电 11.1V/12.6V满" H 1540 2440 50  0000 C CNN
F 2 "" H 1500 2300 50  0001 C CNN
F 3 "" H 1500 2300 50  0001 C CNN
	1    1500 2300
	1    0    0    -1
$EndComp
$Comp
L body-cooler-cache:FUSE F1
U 1 1 5F000008
P 2700 1900
F 0 "F1" H 2740 1970 50  0000 C CNN
F 1 "5A" H 2740 2040 50  0000 C CNN
F 2 "" H 2700 1900 50  0001 C CNN
F 3 "" H 2700 1900 50  0001 C CNN
	1    2700 1900
	1    0    0    -1
$EndComp
$Comp
L body-cooler-cache:PWR-MODULE PS1
U 1 1 5F00000F
P 5900 2300
F 0 "PS1" H 5940 2370 50  0000 C CNN
F 1 "12V -> 5V_A / 5V_B / 3V3" H 5940 2440 50  0000 C CNN
F 2 "" H 5900 2300 50  0001 C CNN
F 3 "" H 5900 2300 50  0001 C CNN
	1    5900 2300
	1    0    0    -1
$EndComp
Wire Wire Line
	1500 1900 1500 1900
Wire Wire Line
	1500 1900 2200 1900
Text Label 1500 1900 0    50   ~ 0
+12V_BAT
Wire Wire Line
	3200 1900 5000 1900
Text Label 3500 1900 0    50   ~ 0
+12V_F
Wire Wire Line
	1500 2700 1500 2700
Wire Wire Line
	1500 2700 5000 2700
Text Label 1500 2700 0    50   ~ 0
GND
Wire Wire Line
	6800 1900 7400 1900
Text Label 7400 1900 0    50   ~ 0
+5V_A
Wire Wire Line
	6800 2100 7400 2100
Text Label 7400 2100 0    50   ~ 0
+5V_B
Wire Wire Line
	6800 2300 7400 2300
Text Label 7400 2300 0    50   ~ 0
+3V3
Wire Wire Line
	6800 2700 7400 2700
Text Label 7400 2700 0    50   ~ 0
GND
Text Notes 3900 3400 0    75   ~ 0
【二】ESP32-S3-DevKitC-1（只画本项目用到的脚）
Text Notes 3900 3520 0    48   ~ 0
左右两侧都是 500mil 短支线 + 网络标签，靠名字连接
$Comp
L body-cooler-cache:ESP32-S3-DEVKITC U1
U 1 1 5F000016
P 6200 5200
F 0 "U1" H 6240 5270 50  0000 C CNN
F 1 "ESP32-S3-N16R8" H 6240 5340 50  0000 C CNN
F 2 "" H 6200 5200 50  0001 C CNN
F 3 "" H 6200 5200 50  0001 C CNN
	1    6200 5200
	1    0    0    -1
$EndComp
Wire Wire Line
	5000 4500 4300 4500
Text Label 4300 4500 2    50   ~ 0
OW_DQ
Wire Wire Line
	5000 4700 4300 4700
Text Label 4300 4700 2    50   ~ 0
VBAT_SENSE
Wire Wire Line
	5000 4900 4300 4900
Text Label 4300 4900 2    50   ~ 0
FLOW_SIG
Wire Wire Line
	5000 5100 4300 5100
Text Label 4300 5100 2    50   ~ 0
LEVEL_SW
Wire Wire Line
	5000 5300 4300 5300
Text Label 4300 5300 2    50   ~ 0
LEAK_A
Wire Wire Line
	5000 5500 4300 5500
Text Label 4300 5500 2    50   ~ 0
ESTOP_SW
Wire Wire Line
	5000 5700 4300 5700
Text Label 4300 5700 2    50   ~ 0
BTN_A
Wire Wire Line
	5000 5900 4300 5900
Text Label 4300 5900 2    50   ~ 0
BTN_B
Wire Wire Line
	7400 4500 8100 4500
Text Label 8100 4500 0    50   ~ 0
K1_IN
Wire Wire Line
	7400 4700 8100 4700
Text Label 8100 4700 0    50   ~ 0
K2_IN
Wire Wire Line
	7400 4900 8100 4900
Text Label 8100 4900 0    50   ~ 0
K3_IN
Wire Wire Line
	7400 5100 8100 5100
Text Label 8100 5100 0    50   ~ 0
K4_IN
Wire Wire Line
	7400 5300 8100 5300
Text Label 8100 5300 0    50   ~ 0
K5_IN
Wire Wire Line
	7400 5500 8100 5500
Text Label 8100 5500 0    50   ~ 0
BUZZ
Wire Wire Line
	7400 5700 8100 5700
Text Label 8100 5700 0    50   ~ 0
NC_WS2812板载
Wire Wire Line
	5800 6300 5800 6900
Text Label 5800 6900 0    50   ~ 0
GND
Wire Wire Line
	6200 6300 6200 6900
Text Label 6200 6900 0    50   ~ 0
+5V_B
Wire Wire Line
	6600 6300 6600 6900
Text Label 6600 6900 0    50   ~ 0
+3V3
Text Notes 9600 1250 0    75   ~ 0
【三】继电器模块 K1~K5（低电平触发）
Text Notes 9600 1370 0    48   ~ 0
IN 拉低 = 吸合；释放时 GPIO 变高阻，由 10k 上拉到 5V 才彻底截止
$Comp
L body-cooler-cache:RELAY-5V-LOW K1
U 1 1 5F00001D
P 10400 1900
F 0 "K1" H 10440 1970 50  0000 C CNN
F 1 "5V低电平触发" H 10440 2040 50  0000 C CNN
F 2 "" H 10400 1900 50  0001 C CNN
F 3 "" H 10400 1900 50  0001 C CNN
	1    10400 1900
	1    0    0    -1
$EndComp
Wire Wire Line
	9900 1700 9600 1700
Text Label 9600 1700 2    50   ~ 0
+5V_A
Wire Wire Line
	9900 2100 9600 2100
Text Label 9600 2100 2    50   ~ 0
GND
Wire Wire Line
	9900 1900 9300 1900
Text Label 9300 1900 2    50   ~ 0
K1_IN
Wire Wire Line
	10900 1700 11200 1700
Text Label 11200 1700 0    50   ~ 0
+12V_F
Wire Wire Line
	10900 1900 11200 1900
Text Label 11200 1900 0    50   ~ 0
PUMP_P
Text Notes 11320 2120 0    45   ~ 0
NC 不接
$Comp
L body-cooler-cache:RELAY-5V-LOW K2
U 1 1 5F000024
P 10400 3300
F 0 "K2" H 10440 3370 50  0000 C CNN
F 1 "5V低电平触发" H 10440 3440 50  0000 C CNN
F 2 "" H 10400 3300 50  0001 C CNN
F 3 "" H 10400 3300 50  0001 C CNN
	1    10400 3300
	1    0    0    -1
$EndComp
Wire Wire Line
	9900 3100 9600 3100
Text Label 9600 3100 2    50   ~ 0
+5V_A
Wire Wire Line
	9900 3500 9600 3500
Text Label 9600 3500 2    50   ~ 0
GND
Wire Wire Line
	9900 3300 9300 3300
Text Label 9300 3300 2    50   ~ 0
K2_IN
Wire Wire Line
	10900 3100 11200 3100
Text Label 11200 3100 0    50   ~ 0
+12V_F
Wire Wire Line
	10900 3300 11200 3300
Text Label 11200 3300 0    50   ~ 0
K2_OUT_备用
Text Notes 11320 3520 0    45   ~ 0
NC 不接
$Comp
L body-cooler-cache:RELAY-5V-LOW K3
U 1 1 5F00002B
P 10400 4700
F 0 "K3" H 10440 4770 50  0000 C CNN
F 1 "5V低电平触发" H 10440 4840 50  0000 C CNN
F 2 "" H 10400 4700 50  0001 C CNN
F 3 "" H 10400 4700 50  0001 C CNN
	1    10400 4700
	1    0    0    -1
$EndComp
Wire Wire Line
	9900 4500 9600 4500
Text Label 9600 4500 2    50   ~ 0
+5V_A
Wire Wire Line
	9900 4900 9600 4900
Text Label 9600 4900 2    50   ~ 0
GND
Wire Wire Line
	9900 4700 9300 4700
Text Label 9300 4700 2    50   ~ 0
K3_IN
Wire Wire Line
	10900 4500 11200 4500
Text Label 11200 4500 0    50   ~ 0
+12V_F
Wire Wire Line
	10900 4700 11200 4700
Text Label 11200 4700 0    50   ~ 0
K3_OUT_备用
Text Notes 11320 4920 0    45   ~ 0
NC 不接
$Comp
L body-cooler-cache:RELAY-5V-LOW K4
U 1 1 5F000032
P 10400 6100
F 0 "K4" H 10440 6170 50  0000 C CNN
F 1 "5V低电平触发" H 10440 6240 50  0000 C CNN
F 2 "" H 10400 6100 50  0001 C CNN
F 3 "" H 10400 6100 50  0001 C CNN
	1    10400 6100
	1    0    0    -1
$EndComp
Wire Wire Line
	9900 5900 9600 5900
Text Label 9600 5900 2    50   ~ 0
+5V_A
Wire Wire Line
	9900 6300 9600 6300
Text Label 9600 6300 2    50   ~ 0
GND
Wire Wire Line
	9900 6100 9300 6100
Text Label 9300 6100 2    50   ~ 0
K4_IN
Wire Wire Line
	10900 5900 11200 5900
Text Label 11200 5900 0    50   ~ 0
+12V_F
Wire Wire Line
	10900 6100 11200 6100
Text Label 11200 6100 0    50   ~ 0
K4_OUT_备用
Text Notes 11320 6320 0    45   ~ 0
NC 不接
$Comp
L body-cooler-cache:RELAY-5V-LOW K5
U 1 1 5F000039
P 10400 7500
F 0 "K5" H 10440 7570 50  0000 C CNN
F 1 "5V低电平触发" H 10440 7640 50  0000 C CNN
F 2 "" H 10400 7500 50  0001 C CNN
F 3 "" H 10400 7500 50  0001 C CNN
	1    10400 7500
	1    0    0    -1
$EndComp
Wire Wire Line
	9900 7300 9600 7300
Text Label 9600 7300 2    50   ~ 0
+5V_A
Wire Wire Line
	9900 7700 9600 7700
Text Label 9600 7700 2    50   ~ 0
GND
Wire Wire Line
	9900 7500 9300 7500
Text Label 9300 7500 2    50   ~ 0
K5_IN
Wire Wire Line
	10900 7300 11200 7300
Text Label 11200 7300 0    50   ~ 0
+12V_F
Wire Wire Line
	10900 7500 11200 7500
Text Label 11200 7500 0    50   ~ 0
K5_OUT_备用
Text Notes 11320 7720 0    45   ~ 0
NC 不接
Text Notes 13300 1250 0    75   ~ 0
【四】泵主回路：电池+ -> 保险丝 -> 继电器 COM/NO -> 泵+ -> 泵- -> 电池-
$Comp
L body-cooler-cache:PUMP-365 M1
U 1 1 5F000040
P 14300 1900
F 0 "M1" H 14340 1970 50  0000 C CNN
F 1 "365 隔膜泵" H 14340 2040 50  0000 C CNN
F 2 "" H 14300 1900 50  0001 C CNN
F 3 "" H 14300 1900 50  0001 C CNN
	1    14300 1900
	1    0    0    -1
$EndComp
Wire Wire Line
	11200 1900 13800 1900
Text Label 12300 1900 0    50   ~ 0
PUMP_P
Wire Wire Line
	14800 1900 15700 1900
Text Label 15700 1900 0    50   ~ 0
GND
$Comp
L body-cooler-cache:D-SCHOTTKY D1
U 1 1 5F000047
P 14300 2700
F 0 "D1" H 14340 2770 50  0000 C CNN
F 1 "1N5822 续流" H 14340 2840 50  0000 C CNN
F 2 "" H 14300 2700 50  0001 C CNN
F 3 "" H 14300 2700 50  0001 C CNN
	1    14300 2700
	-1    0    0    1
$EndComp
Wire Wire Line
	13800 2700 13800 1900
Connection ~ 13800 1900
Wire Wire Line
	14800 2700 14800 1900
Connection ~ 14800 1900
Text Notes 13500 3000 0    48   ~ 0
阴极(有环那一端)朝泵+
Text Notes 11800 7900 0    70   ~ 0
【三之二】继电器 IN 的 10k 上拉（5 只：一端 +5V_A，一端 Kn_IN）
Text Notes 11800 8010 0    48   ~ 0
ESP32 复位期间 GPIO 是高阻，靠它把 IN 明确拉到 5V，继电器才彻底截止
$Comp
L body-cooler-cache:R RP1
U 1 1 5F00004E
P 12300 8800
F 0 "RP1" H 12340 8870 50  0000 C CNN
F 1 "10k" H 12340 8940 50  0000 C CNN
F 2 "" H 12300 8800 50  0001 C CNN
F 3 "" H 12300 8800 50  0001 C CNN
	1    12300 8800
	1    0    0    -1
$EndComp
Wire Wire Line
	12300 8600 12300 8200
Text Label 12300 8200 0    50   ~ 0
+5V_A
Wire Wire Line
	12300 9000 12300 9400
Text Label 12300 9400 0    50   ~ 0
K1_IN
$Comp
L body-cooler-cache:R RP2
U 1 1 5F000055
P 13300 8800
F 0 "RP2" H 13340 8870 50  0000 C CNN
F 1 "10k" H 13340 8940 50  0000 C CNN
F 2 "" H 13300 8800 50  0001 C CNN
F 3 "" H 13300 8800 50  0001 C CNN
	1    13300 8800
	1    0    0    -1
$EndComp
Wire Wire Line
	13300 8600 13300 8200
Text Label 13300 8200 0    50   ~ 0
+5V_A
Wire Wire Line
	13300 9000 13300 9400
Text Label 13300 9400 0    50   ~ 0
K2_IN
$Comp
L body-cooler-cache:R RP3
U 1 1 5F00005C
P 14300 8800
F 0 "RP3" H 14340 8870 50  0000 C CNN
F 1 "10k" H 14340 8940 50  0000 C CNN
F 2 "" H 14300 8800 50  0001 C CNN
F 3 "" H 14300 8800 50  0001 C CNN
	1    14300 8800
	1    0    0    -1
$EndComp
Wire Wire Line
	14300 8600 14300 8200
Text Label 14300 8200 0    50   ~ 0
+5V_A
Wire Wire Line
	14300 9000 14300 9400
Text Label 14300 9400 0    50   ~ 0
K3_IN
$Comp
L body-cooler-cache:R RP4
U 1 1 5F000063
P 15300 8800
F 0 "RP4" H 15340 8870 50  0000 C CNN
F 1 "10k" H 15340 8940 50  0000 C CNN
F 2 "" H 15300 8800 50  0001 C CNN
F 3 "" H 15300 8800 50  0001 C CNN
	1    15300 8800
	1    0    0    -1
$EndComp
Wire Wire Line
	15300 8600 15300 8200
Text Label 15300 8200 0    50   ~ 0
+5V_A
Wire Wire Line
	15300 9000 15300 9400
Text Label 15300 9400 0    50   ~ 0
K4_IN
$Comp
L body-cooler-cache:R RP5
U 1 1 5F00006A
P 16300 8800
F 0 "RP5" H 16340 8870 50  0000 C CNN
F 1 "10k" H 16340 8940 50  0000 C CNN
F 2 "" H 16300 8800 50  0001 C CNN
F 3 "" H 16300 8800 50  0001 C CNN
	1    16300 8800
	1    0    0    -1
$EndComp
Wire Wire Line
	16300 8600 16300 8200
Text Label 16300 8200 0    50   ~ 0
+5V_A
Wire Wire Line
	16300 9000 16300 9400
Text Label 16300 9400 0    50   ~ 0
K5_IN
Text Notes 700 7900 0    75   ~ 0
【五】输入端
Text Notes 700 8150 0    65   ~ 0
5.1 DS18B20 单总线温度（4.7k 上拉到 3V3，整条总线只加一只）
$Comp
L body-cooler-cache:R R11
U 1 1 5F000071
P 1300 9000
F 0 "R11" H 1340 9070 50  0000 C CNN
F 1 "4.7k" H 1340 9140 50  0000 C CNN
F 2 "" H 1300 9000 50  0001 C CNN
F 3 "" H 1300 9000 50  0001 C CNN
	1    1300 9000
	1    0    0    -1
$EndComp
Wire Wire Line
	1300 8800 1300 8400
Text Label 1300 8400 0    50   ~ 0
+3V3
Wire Wire Line
	1300 9200 1300 9600
Text Label 1300 9600 0    50   ~ 0
OW_DQ
$Comp
L body-cooler-cache:DS18B20 T1
U 1 1 5F000078
P 3000 8800
F 0 "T1" H 3040 8870 50  0000 C CNN
F 1 "防水探头1" H 3040 8940 50  0000 C CNN
F 2 "" H 3000 8800 50  0001 C CNN
F 3 "" H 3000 8800 50  0001 C CNN
	1    3000 8800
	1    0    0    -1
$EndComp
Wire Wire Line
	2500 8600 2000 8600
Text Label 2000 8600 2    50   ~ 0
+3V3
Wire Wire Line
	2500 8800 2000 8800
Text Label 2000 8800 2    50   ~ 0
OW_DQ
Wire Wire Line
	2500 9000 2000 9000
Text Label 2000 9000 2    50   ~ 0
GND
$Comp
L body-cooler-cache:DS18B20 T2
U 1 1 5F00007F
P 3000 9800
F 0 "T2" H 3040 9870 50  0000 C CNN
F 1 "防水探头2" H 3040 9940 50  0000 C CNN
F 2 "" H 3000 9800 50  0001 C CNN
F 3 "" H 3000 9800 50  0001 C CNN
	1    3000 9800
	1    0    0    -1
$EndComp
Wire Wire Line
	2500 9600 2000 9600
Text Label 2000 9600 2    50   ~ 0
+3V3
Wire Wire Line
	2500 9800 2000 9800
Text Label 2000 9800 2    50   ~ 0
OW_DQ
Wire Wire Line
	2500 10000 2000 10000
Text Label 2000 10000 2    50   ~ 0
GND
$Comp
L body-cooler-cache:DS18B20 T3
U 1 1 5F000086
P 3000 10800
F 0 "T3" H 3040 10870 50  0000 C CNN
F 1 "防水探头3" H 3040 10940 50  0000 C CNN
F 2 "" H 3000 10800 50  0001 C CNN
F 3 "" H 3000 10800 50  0001 C CNN
	1    3000 10800
	1    0    0    -1
$EndComp
Wire Wire Line
	2500 10600 2000 10600
Text Label 2000 10600 2    50   ~ 0
+3V3
Wire Wire Line
	2500 10800 2000 10800
Text Label 2000 10800 2    50   ~ 0
OW_DQ
Wire Wire Line
	2500 11000 2000 11000
Text Label 2000 11000 2    50   ~ 0
GND
Text Notes 1900 11300 0    45   ~ 0
现只有 3 个防水探头，还缺 2 个；再多就并联到 OW_DQ
Text Notes 4500 8150 0    65   ~ 0
5.2 电池电压采样（100k / 18k = 6.556:1，必须走 ADC1）
$Comp
L body-cooler-cache:R R6
U 1 1 5F00008D
P 5000 9000
F 0 "R6" H 5040 9070 50  0000 C CNN
F 1 "100k" H 5040 9140 50  0000 C CNN
F 2 "" H 5000 9000 50  0001 C CNN
F 3 "" H 5000 9000 50  0001 C CNN
	1    5000 9000
	1    0    0    -1
$EndComp
$Comp
L body-cooler-cache:R R7
U 1 1 5F000094
P 5000 9800
F 0 "R7" H 5040 9870 50  0000 C CNN
F 1 "18k" H 5040 9940 50  0000 C CNN
F 2 "" H 5000 9800 50  0001 C CNN
F 3 "" H 5000 9800 50  0001 C CNN
	1    5000 9800
	1    0    0    -1
$EndComp
Wire Wire Line
	5000 8800 5000 8400
Text Label 5000 8400 0    50   ~ 0
+12V_F
Wire Wire Line
	5000 9200 5000 9600
Wire Wire Line
	5000 9200 5700 9200
Text Label 5700 9200 0    50   ~ 0
VBAT_SENSE
Connection ~ 5000 9200
Wire Wire Line
	5000 10000 5000 10400
Text Label 5000 10400 0    50   ~ 0
GND
Text Notes 6700 8150 0    65   ~ 0
5.3 水流传感器（5V 方波经 2.2k+10k/20k 分压到 3.11V 进 GPIO10）
$Comp
L body-cooler-cache:R R8
U 1 1 5F00009B
P 7000 9000
F 0 "R8" H 7040 9070 50  0000 C CNN
F 1 "2.2k" H 7040 9140 50  0000 C CNN
F 2 "" H 7000 9000 50  0001 C CNN
F 3 "" H 7000 9000 50  0001 C CNN
	1    7000 9000
	1    0    0    -1
$EndComp
$Comp
L body-cooler-cache:R R9
U 1 1 5F0000A2
P 7000 9800
F 0 "R9" H 7040 9870 50  0000 C CNN
F 1 "10k" H 7040 9940 50  0000 C CNN
F 2 "" H 7000 9800 50  0001 C CNN
F 3 "" H 7000 9800 50  0001 C CNN
	1    7000 9800
	1    0    0    -1
$EndComp
$Comp
L body-cooler-cache:R R10
U 1 1 5F0000A9
P 7000 10600
F 0 "R10" H 7040 10670 50  0000 C CNN
F 1 "20k" H 7040 10740 50  0000 C CNN
F 2 "" H 7000 10600 50  0001 C CNN
F 3 "" H 7000 10600 50  0001 C CNN
	1    7000 10600
	1    0    0    -1
$EndComp
$Comp
L body-cooler-cache:FLOW-YF-S401 FS1
U 1 1 5F0000B0
P 8900 9400
F 0 "FS1" H 8940 9470 50  0000 C CNN
F 1 "YF-S401" H 8940 9540 50  0000 C CNN
F 2 "" H 8900 9400 50  0001 C CNN
F 3 "" H 8900 9400 50  0001 C CNN
	1    8900 9400
	-1    0    0    1
$EndComp
Wire Wire Line
	7000 8800 7000 8400
Text Label 7000 8400 0    50   ~ 0
+5V_A
Wire Wire Line
	7000 9200 7000 9600
Wire Wire Line
	7000 9200 8300 9400
Text Label 7500 9200 0    50   ~ 0
FLOW_PU
Connection ~ 7000 9200
Wire Wire Line
	7000 10000 7000 10400
Wire Wire Line
	7000 10000 7700 10000
Text Label 7700 10000 0    50   ~ 0
FLOW_SIG
Connection ~ 7000 10000
Wire Wire Line
	7000 10800 7000 11200
Text Label 7000 11200 0    50   ~ 0
GND
Wire Wire Line
	9500 9600 10000 9600
Text Label 10000 9600 0    50   ~ 0
+5V_A
Wire Wire Line
	9500 9200 10000 9200
Text Label 10000 9200 0    50   ~ 0
GND
Text Notes 700 12000 0    65   ~ 0
5.4 开关量（全部用 MCU 内部上拉：引脚 — 开关 — GND）
$Comp
L body-cooler-cache:SW-LEVER SW1
U 1 1 5F0000B7
P 2100 12500
F 0 "SW1" H 2140 12570 50  0000 C CNN
F 1 "浮子液位(常开)" H 2140 12640 50  0000 C CNN
F 2 "" H 2100 12500 50  0001 C CNN
F 3 "" H 2100 12500 50  0001 C CNN
	1    2100 12500
	1    0    0    -1
$EndComp
Wire Wire Line
	1600 12500 1000 12500
Text Label 1000 12500 2    50   ~ 0
LEVEL_SW
Wire Wire Line
	2600 12500 3200 12500
Text Label 3200 12500 0    50   ~ 0
GND
$Comp
L body-cooler-cache:SW-NC SW2
U 1 1 5F0000BE
P 5100 12500
F 0 "SW2" H 5140 12570 50  0000 C CNN
F 1 "急停/总电源(常闭)" H 5140 12640 50  0000 C CNN
F 2 "" H 5100 12500 50  0001 C CNN
F 3 "" H 5100 12500 50  0001 C CNN
	1    5100 12500
	1    0    0    -1
$EndComp
Wire Wire Line
	4600 12500 4000 12500
Text Label 4000 12500 2    50   ~ 0
ESTOP_SW
Wire Wire Line
	5600 12500 6200 12500
Text Label 6200 12500 0    50   ~ 0
GND
$Comp
L body-cooler-cache:SW-PUSH SW3
U 1 1 5F0000C5
P 2100 14000
F 0 "SW3" H 2140 14070 50  0000 C CNN
F 1 "按键A" H 2140 14140 50  0000 C CNN
F 2 "" H 2100 14000 50  0001 C CNN
F 3 "" H 2100 14000 50  0001 C CNN
	1    2100 14000
	1    0    0    -1
$EndComp
Wire Wire Line
	1600 14000 1000 14000
Text Label 1000 14000 2    50   ~ 0
BTN_A
Wire Wire Line
	2600 14000 3200 14000
Text Label 3200 14000 0    50   ~ 0
GND
$Comp
L body-cooler-cache:SW-PUSH SW4
U 1 1 5F0000CC
P 5100 14000
F 0 "SW4" H 5140 14070 50  0000 C CNN
F 1 "按键B" H 5140 14140 50  0000 C CNN
F 2 "" H 5100 14000 50  0001 C CNN
F 3 "" H 5100 14000 50  0001 C CNN
	1    5100 14000
	1    0    0    -1
$EndComp
Wire Wire Line
	4600 14000 4000 14000
Text Label 4000 14000 2    50   ~ 0
BTN_B
Wire Wire Line
	5600 14000 6200 14000
Text Label 6200 14000 0    50   ~ 0
GND
$Comp
L body-cooler-cache:CONN-2 J1
U 1 1 5F0000D3
P 6300 13000
F 0 "J1" H 6340 13070 50  0000 C CNN
F 1 "漏水探针" H 6340 13140 50  0000 C CNN
F 2 "" H 6300 13000 50  0001 C CNN
F 3 "" H 6300 13000 50  0001 C CNN
	1    6300 13000
	1    0    0    -1
$EndComp
Wire Wire Line
	5800 12900 5200 12900
Text Label 5200 12900 2    50   ~ 0
LEAK_A
Wire Wire Line
	5800 13100 5200 13100
Text Label 5200 13100 2    50   ~ 0
GND
Text Notes 5400 13500 0    45   ~ 0
J1 两根裸铜线相距 2~3mm，遇水导通
Text Notes 8300 12000 0    65   ~ 0
5.5 蜂鸣器（可选）
$Comp
L body-cooler-cache:BUZZER LS1
U 1 1 5F0000DA
P 9200 12500
F 0 "LS1" H 9240 12570 50  0000 C CNN
F 1 "有源蜂鸣器" H 9240 12640 50  0000 C CNN
F 2 "" H 9200 12500 50  0001 C CNN
F 3 "" H 9200 12500 50  0001 C CNN
	1    9200 12500
	1    0    0    -1
$EndComp
Wire Wire Line
	8750 12400 8150 12400
Text Label 8150 12400 2    50   ~ 0
BUZZ
Wire Wire Line
	8750 12600 8150 12600
Text Label 8150 12600 2    50   ~ 0
GND
Text Notes 11800 10600 0    75   ~ 0
图例 / 网络名含义
Text Notes 11800 10770 0    45   ~ 0
+12V_BAT   电池正极（保险丝之前）
Text Notes 11800 10880 0    45   ~ 0
+12V_F     保险丝之后的 12V 母线
Text Notes 11800 10990 0    45   ~ 0
+5V_A      只给 5 个继电器线圈的 5V 轨
Text Notes 11800 11100 0    45   ~ 0
+5V_B      只给 ESP32 的 5V 轨
Text Notes 11800 11210 0    45   ~ 0
+3V3       ESP32 的 3.3V（DS18B20 上拉）
Text Notes 11800 11320 0    45   ~ 0
GND        单点星形接地的公共地
Text Notes 11800 11430 0    45   ~ 0
K1_IN ~ K5_IN   GPIO5/6/7/15/16 -> 继电器线圈 IN
Text Notes 11800 11540 0    45   ~ 0
PUMP_P     继电器1 的 NO 触点 -> 泵正极
Text Notes 11800 11650 0    45   ~ 0
K2_OUT ~ K5_OUT_备用   备用继电器输出
Text Notes 11800 11760 0    45   ~ 0
OW_DQ      DS18B20 单总线
Text Notes 11800 11870 0    45   ~ 0
VBAT_SENSE / FLOW_SIG   分压中点 -> ADC
Text Notes 11800 11980 0    45   ~ 0
LEVEL_SW / ESTOP_SW / LEAK_A / BTN_A / BTN_B   开关量输入
Text Notes 11800 12300 0    52   ~ 0
同名网络 = 必须手工接的一根线
Text Notes 11800 12440 0    52   ~ 0
本图按你要求不含任何陶瓷电容与电解电容
Text Notes 11800 12580 0    52   ~ 0
继电器模块必须和 ESP32 共地，否则改极性也没用
$EndSCHEMATC
