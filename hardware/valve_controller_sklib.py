from collections import defaultdict
from skidl import Pin, Part, Alias, SchLib, SKIDL, TEMPLATE

from skidl.pin import pin_types

SKIDL_lib_version = '0.0.1'

valve_controller = SchLib(tool=SKIDL).add_parts(*[
        Part(**{ 'name':'Screw_Terminal_01x02', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'Screw_Terminal_01x02'}), 'ref_prefix':'J', 'fplist':[''], 'footprint':'TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-3-2-5.08_1x02_P5.08mm_Horizontal', 'keywords':'screw terminal', 'description':'Generic screw terminal, single row, 01x02, script generated (kicad-library-utils/schlib/autogen/connector/)', 'datasheet':'', 'pins':[
            Pin(num='1',name='Pin_1',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',name='Pin_2',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'Polyfuse', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'Polyfuse'}), 'ref_prefix':'F', 'fplist':[''], 'footprint':'Fuse:Fuse_1812_4532Metric', 'keywords':'resettable fuse PTC PPTC polyfuse polyswitch', 'description':'Resettable fuse, polymeric positive temperature coefficient', 'datasheet':'', 'pins':[
            Pin(num='1',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'Q_PMOS_SOT23', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'Q_PMOS_SOT23'}), 'ref_prefix':'Q', 'fplist':['Package_TO_SOT_SMD:SOT-23'], 'footprint':'Package_TO_SOT_SMD:SOT-23', 'keywords':'', 'description':'P-channel MOSFET, SOT-23 pin order 1=G 2=S 3=D (e.g. AO3407A)', 'datasheet':'', 'pins':[
            Pin(num='1',name='G',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',name='S',func=pin_types.PASSIVE,unit=1),
            Pin(num='3',name='D',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'R', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'R'}), 'ref_prefix':'R', 'fplist':[''], 'footprint':'Resistor_SMD:R_0603_1608Metric', 'keywords':'R res resistor', 'description':'Resistor', 'datasheet':'', 'pins':[
            Pin(num='1',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'D_Zener', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'D_Zener'}), 'ref_prefix':'D', 'fplist':[''], 'footprint':'Diode_SMD:D_SOD-123', 'keywords':'diode', 'description':'Zener diode', 'datasheet':'', 'pins':[
            Pin(num='1',name='K',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',name='A',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'D_TVS', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'D_TVS'}), 'ref_prefix':'D', 'fplist':[''], 'footprint':'Diode_SMD:D_SMB', 'keywords':'diode TVS thyrector', 'description':'Bidirectional transient-voltage-suppression diode', 'datasheet':'', 'pins':[
            Pin(num='1',name='A1',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',name='A2',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'C', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'C'}), 'ref_prefix':'C', 'fplist':[''], 'footprint':'Capacitor_SMD:C_0603_1608Metric', 'keywords':'cap capacitor', 'description':'Unpolarized capacitor', 'datasheet':'', 'pins':[
            Pin(num='1',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'AP63205WU', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'AP63205WU'}), 'ref_prefix':'U', 'fplist':['Package_TO_SOT_SMD:TSOT-23-6', 'Package_TO_SOT_SMD:TSOT-23-6'], 'footprint':'Package_TO_SOT_SMD:TSOT-23-6', 'keywords':'2A Buck DC/DC', 'description':'2A, 1.1MHz Buck DC/DC Converter, fixed 5.0V output voltage, TSOT-23-6', 'datasheet':'https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf', 'pins':[
            Pin(num='1',name='FB',func=pin_types.INPUT,unit=1),
            Pin(num='2',name='EN',func=pin_types.INPUT,unit=1),
            Pin(num='3',name='IN',func=pin_types.PWRIN,unit=1),
            Pin(num='4',name='GND',func=pin_types.PWRIN,unit=1),
            Pin(num='5',name='SW',func=pin_types.OUTPUT,unit=1),
            Pin(num='6',name='BST',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'L', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'L'}), 'ref_prefix':'L', 'fplist':[''], 'footprint':'Inductor_SMD:L_Bourns-SRN4018', 'keywords':'inductor choke coil reactor magnetic', 'description':'Inductor', 'datasheet':'', 'pins':[
            Pin(num='1',name='1',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',name='2',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'D_Schottky', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'D_Schottky'}), 'ref_prefix':'D', 'fplist':[''], 'footprint':'Diode_SMD:D_SOD-123', 'keywords':'diode Schottky', 'description':'Schottky diode', 'datasheet':'', 'pins':[
            Pin(num='1',name='K',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',name='A',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'AP7361C-33E', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'AP7361C-33E'}), 'ref_prefix':'U', 'fplist':['Package_TO_SOT_SMD:SOT-223-3_TabPin2', 'Package_TO_SOT_SMD:SOT-223-3_TabPin2'], 'footprint':'Package_TO_SOT_SMD:SOT-223-3_TabPin2', 'keywords':'linear regulator ldo fixed positive', 'description':'1A Low Dropout regulator, positive, 3.3V fixed output, SOT-223', 'datasheet':'https://www.diodes.com/assets/Datasheets/AP7361C.pdf', 'pins':[
            Pin(num='1',name='VI',func=pin_types.PWRIN,unit=1),
            Pin(num='2',name='GND',func=pin_types.PWRIN,unit=1),
            Pin(num='3',name='VO',func=pin_types.PWROUT,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'ESP32-S3-WROOM-1', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'ESP32-S3-WROOM-1'}), 'ref_prefix':'U', 'fplist':['RF_Module:ESP32-S3-WROOM-1'], 'footprint':'RF_Module:ESP32-S3-WROOM-1', 'keywords':'RF Radio BT ESP ESP32-S3 Espressif onboard PCB antenna', 'description':'RF Module, ESP32-S3 SoC, Wi-Fi 802.11b/g/n, Bluetooth, BLE, 32-bit, 3.3V, onboard antenna, SMD', 'datasheet':'https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf', 'pins':[
            Pin(num='1',name='GND',func=pin_types.PWRIN,unit=1),
            Pin(num='2',name='3V3',func=pin_types.PWRIN,unit=1),
            Pin(num='3',name='EN',func=pin_types.INPUT,unit=1),
            Pin(num='4',name='IO4',func=pin_types.BIDIR,unit=1),
            Pin(num='5',name='IO5',func=pin_types.BIDIR,unit=1),
            Pin(num='6',name='IO6',func=pin_types.BIDIR,unit=1),
            Pin(num='7',name='IO7',func=pin_types.BIDIR,unit=1),
            Pin(num='8',name='IO15',func=pin_types.BIDIR,unit=1),
            Pin(num='9',name='IO16',func=pin_types.BIDIR,unit=1),
            Pin(num='10',name='IO17',func=pin_types.BIDIR,unit=1),
            Pin(num='11',name='IO18',func=pin_types.BIDIR,unit=1),
            Pin(num='12',name='IO8',func=pin_types.BIDIR,unit=1),
            Pin(num='13',name='USB_D-',func=pin_types.BIDIR,unit=1),
            Pin(num='14',name='USB_D+',func=pin_types.BIDIR,unit=1),
            Pin(num='15',name='IO3',func=pin_types.BIDIR,unit=1),
            Pin(num='16',name='IO46',func=pin_types.BIDIR,unit=1),
            Pin(num='17',name='IO9',func=pin_types.BIDIR,unit=1),
            Pin(num='18',name='IO10',func=pin_types.BIDIR,unit=1),
            Pin(num='19',name='IO11',func=pin_types.BIDIR,unit=1),
            Pin(num='20',name='IO12',func=pin_types.BIDIR,unit=1),
            Pin(num='21',name='IO13',func=pin_types.BIDIR,unit=1),
            Pin(num='22',name='IO14',func=pin_types.BIDIR,unit=1),
            Pin(num='23',name='IO21',func=pin_types.BIDIR,unit=1),
            Pin(num='24',name='IO47',func=pin_types.BIDIR,unit=1),
            Pin(num='25',name='IO48',func=pin_types.BIDIR,unit=1),
            Pin(num='26',name='IO45',func=pin_types.BIDIR,unit=1),
            Pin(num='27',name='IO0',func=pin_types.BIDIR,unit=1),
            Pin(num='28',name='IO35',func=pin_types.BIDIR,unit=1),
            Pin(num='29',name='IO36',func=pin_types.BIDIR,unit=1),
            Pin(num='30',name='IO37',func=pin_types.BIDIR,unit=1),
            Pin(num='31',name='IO38',func=pin_types.BIDIR,unit=1),
            Pin(num='32',name='IO39',func=pin_types.BIDIR,unit=1),
            Pin(num='33',name='IO40',func=pin_types.BIDIR,unit=1),
            Pin(num='34',name='IO41',func=pin_types.BIDIR,unit=1),
            Pin(num='35',name='IO42',func=pin_types.BIDIR,unit=1),
            Pin(num='36',name='RXD0',func=pin_types.BIDIR,unit=1),
            Pin(num='37',name='TXD0',func=pin_types.BIDIR,unit=1),
            Pin(num='38',name='IO2',func=pin_types.BIDIR,unit=1),
            Pin(num='39',name='IO1',func=pin_types.BIDIR,unit=1),
            Pin(num='40',name='GND',func=pin_types.PASSIVE,unit=1),
            Pin(num='41',name='GND',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'SW_Push', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'SW_Push'}), 'ref_prefix':'SW', 'fplist':[''], 'footprint':'Button_Switch_SMD:SW_SPST_PTS645Sx43SMTR92', 'keywords':'switch normally-open pushbutton push-button', 'description':'Push button switch, generic, two pins', 'datasheet':'', 'pins':[
            Pin(num='1',name='1',func=pin_types.PASSIVE),
            Pin(num='2',name='2',func=pin_types.PASSIVE)], 'unit_defs':[] }),
        Part(**{ 'name':'Conn_01x04', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'Conn_01x04'}), 'ref_prefix':'J', 'fplist':[''], 'footprint':'Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical', 'keywords':'connector', 'description':'Generic connector, single row, 01x04, script generated (kicad-library-utils/schlib/autogen/connector/)', 'datasheet':'', 'pins':[
            Pin(num='1',name='Pin_1',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',name='Pin_2',func=pin_types.PASSIVE,unit=1),
            Pin(num='3',name='Pin_3',func=pin_types.PASSIVE,unit=1),
            Pin(num='4',name='Pin_4',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'USB_C_Receptacle_USB2.0_16P', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'USB_C_Receptacle_USB2.0_16P'}), 'ref_prefix':'J', 'fplist':[''], 'footprint':'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12', 'keywords':'usb universal serial bus type-C USB2.0', 'description':'USB 2.0-only 16P Type-C Receptacle connector', 'datasheet':'https://www.usb.org/sites/default/files/documents/usb_type-c.zip', 'pins':[
            Pin(num='A1',name='GND',func=pin_types.PASSIVE,unit=1),
            Pin(num='A4',name='VBUS',func=pin_types.PASSIVE,unit=1),
            Pin(num='A5',name='CC1',func=pin_types.BIDIR,unit=1),
            Pin(num='A6',name='D+',func=pin_types.BIDIR,unit=1),
            Pin(num='A7',name='D-',func=pin_types.BIDIR,unit=1),
            Pin(num='A8',name='SBU1',func=pin_types.BIDIR,unit=1),
            Pin(num='A9',name='VBUS',func=pin_types.PASSIVE,unit=1),
            Pin(num='A12',name='GND',func=pin_types.PASSIVE,unit=1),
            Pin(num='B1',name='GND',func=pin_types.PASSIVE,unit=1),
            Pin(num='B4',name='VBUS',func=pin_types.PASSIVE,unit=1),
            Pin(num='B5',name='CC2',func=pin_types.BIDIR,unit=1),
            Pin(num='B6',name='D+',func=pin_types.BIDIR,unit=1),
            Pin(num='B7',name='D-',func=pin_types.BIDIR,unit=1),
            Pin(num='B8',name='SBU2',func=pin_types.BIDIR,unit=1),
            Pin(num='B9',name='VBUS',func=pin_types.PASSIVE,unit=1),
            Pin(num='B12',name='GND',func=pin_types.PASSIVE,unit=1),
            Pin(num='SH',name='SHIELD',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'USBLC6-2P6', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'USBLC6-2P6'}), 'ref_prefix':'U', 'fplist':['Package_TO_SOT_SMD:SOT-666'], 'footprint':'Package_TO_SOT_SMD:SOT-666', 'keywords':'usb ethernet video', 'description':'Very low capacitance ESD protection diode, 2 data-line, SOT-666', 'datasheet':'https://www.st.com/resource/en/datasheet/usblc6-2.pdf', 'pins':[
            Pin(num='1',name='I/O1',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',name='GND',func=pin_types.PASSIVE,unit=1),
            Pin(num='3',name='I/O2',func=pin_types.PASSIVE,unit=1),
            Pin(num='4',name='I/O2',func=pin_types.PASSIVE,unit=1),
            Pin(num='5',name='VBUS',func=pin_types.PASSIVE,unit=1),
            Pin(num='6',name='I/O1',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'AO3400A', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'AO3400A'}), 'ref_prefix':'Q', 'fplist':['', 'Package_TO_SOT_SMD:SOT-23'], 'footprint':'Package_TO_SOT_SMD:SOT-23', 'keywords':'N-Channel MOSFET', 'description':'30V Vds, 5.7A Id, N-Channel MOSFET, SOT-23', 'datasheet':'http://www.aosmd.com/pdfs/datasheet/AO3400A.pdf', 'pins':[
            Pin(num='1',name='G',func=pin_types.INPUT,unit=1),
            Pin(num='2',name='S',func=pin_types.PASSIVE,unit=1),
            Pin(num='3',name='D',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'CA-IS3092W', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'CA-IS3092W'}), 'ref_prefix':'U', 'fplist':['Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm'], 'footprint':'Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm', 'keywords':'', 'description':'Isolated half-duplex RS-485 transceiver with integrated DC-DC, 5kVrms, 3.3V/5V, SOIC-16W', 'datasheet':'https://www.lcsc.com/product-detail/C2890051.html', 'pins':[
            Pin(num='1',name='VCC',func=pin_types.PWRIN,unit=1),
            Pin(num='2',name='GNDA',func=pin_types.PWRIN,unit=1),
            Pin(num='3',name='RO',func=pin_types.OUTPUT,unit=1),
            Pin(num='4',name='~{RE}',func=pin_types.INPUT,unit=1),
            Pin(num='5',name='DE',func=pin_types.INPUT,unit=1),
            Pin(num='6',name='DI',func=pin_types.INPUT,unit=1),
            Pin(num='7',name='NC',func=pin_types.NOCONNECT,unit=1),
            Pin(num='8',name='GNDA',func=pin_types.PWRIN,unit=1),
            Pin(num='16',name='VISO',func=pin_types.PWROUT,unit=1),
            Pin(num='15',name='GNDB',func=pin_types.PWRIN,unit=1),
            Pin(num='14',name='NC',func=pin_types.NOCONNECT,unit=1),
            Pin(num='13',name='B',func=pin_types.BIDIR,unit=1),
            Pin(num='12',name='A',func=pin_types.BIDIR,unit=1),
            Pin(num='11',name='NC',func=pin_types.NOCONNECT,unit=1),
            Pin(num='10',name='SEL',func=pin_types.INPUT,unit=1),
            Pin(num='9',name='GNDB',func=pin_types.PWRIN,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'SM712_SOT23', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'SM712_SOT23'}), 'ref_prefix':'D', 'fplist':['Package_TO_SOT_SMD:SOT-23'], 'footprint':'Package_TO_SOT_SMD:SOT-23', 'keywords':'transient voltage suppressor thyrector transil', 'description':'7V/12V, 600W Asymmetrical TVS Diode Array, SOT-23', 'datasheet':'https://www.littelfuse.com/~/media/electronics/datasheets/tvs_diode_arrays/littelfuse_tvs_diode_array_sm712_datasheet.pdf.pdf', 'pins':[
            Pin(num='1',name='A1',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',name='A2',func=pin_types.PASSIVE,unit=1),
            Pin(num='3',name='common',func=pin_types.INPUT,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'SolderJumper_2_Open', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'SolderJumper_2_Open'}), 'ref_prefix':'JP', 'fplist':[''], 'footprint':'Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm', 'keywords':'solder jumper SPST', 'description':'Solder Jumper, 2-pole, open', 'datasheet':'', 'pins':[
            Pin(num='1',name='A',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',name='B',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'Conn_01x03', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'Conn_01x03'}), 'ref_prefix':'J', 'fplist':[''], 'footprint':'TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-3-3.5-H_1x03_P3.50mm_Horizontal', 'keywords':'connector', 'description':'Generic connector, single row, 01x03, script generated (kicad-library-utils/schlib/autogen/connector/)', 'datasheet':'', 'pins':[
            Pin(num='1',name='Pin_1',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',name='Pin_2',func=pin_types.PASSIVE,unit=1),
            Pin(num='3',name='Pin_3',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'LED', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'LED'}), 'ref_prefix':'D', 'fplist':[''], 'footprint':'LED_SMD:LED_0603_1608Metric', 'keywords':'LED diode', 'description':'Light emitting diode', 'datasheet':'', 'pins':[
            Pin(num='1',name='K',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',name='A',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] }),
        Part(**{ 'name':'TestPoint', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'TestPoint'}), 'ref_prefix':'TP', 'fplist':[''], 'footprint':'TestPoint:TestPoint_Pad_D1.5mm', 'keywords':'test point tp', 'description':'test point', 'datasheet':'', 'pins':[
            Pin(num='1',name='1',func=pin_types.PASSIVE,unit=1)], 'unit_defs':[] })])