"""Component datasheet model (SI units, unknown = None).

A component never receives default technical values: every numeric spec is
``None`` until a human supplies it. Completeness is computed from the
category-specific list of required fields (see ``required_fields``).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Category(str, Enum):
    BATTERY = "battery"
    BMS = "bms"
    DCDC_CONVERTER = "dcdc_converter"
    REGULATOR = "regulator"
    POWER_SUPPLY = "power_supply"
    FUSE = "fuse"
    SWITCH = "switch"
    EMERGENCY_STOP = "emergency_stop"
    SBC = "sbc"
    MICROCONTROLLER = "microcontroller"
    STORAGE = "storage"
    COOLING = "cooling"
    MOTOR_DRIVER = "motor_driver"
    DC_MOTOR = "dc_motor"
    SERVO = "servo"
    SERVO_DRIVER = "servo_driver"
    WHEEL = "wheel"
    CASTER = "caster"
    LIDAR = "lidar"
    CAMERA = "camera"
    ULTRASONIC = "ultrasonic"
    TOF = "tof"
    ENCODER = "encoder"
    IMU = "imu"
    INFRARED = "infrared"
    BUMPER = "bumper"
    DISPLAY = "display"
    LED_MATRIX = "led_matrix"
    MICROPHONE = "microphone"
    SPEAKER = "speaker"
    AUDIO_AMPLIFIER = "audio_amplifier"
    COMM_MODULE = "comm_module"
    CHASSIS = "chassis"
    MOUNT = "mount"
    CABLE = "cable"
    CONNECTOR = "connector"
    HARDWARE = "hardware"
    OTHER = "other"


class ElectricalRole(str, Enum):
    SOURCE = "source"  # provides power (battery, converters)
    LOAD = "load"  # consumes power
    PASSIVE = "passive"  # no electrical load model (mechanical / wiring / protection)


_SOURCES = {Category.BATTERY, Category.DCDC_CONVERTER, Category.REGULATOR, Category.POWER_SUPPLY}
_PASSIVE = {
    Category.BMS,
    Category.FUSE,
    Category.SWITCH,
    Category.EMERGENCY_STOP,
    Category.WHEEL,
    Category.CASTER,
    Category.CHASSIS,
    Category.MOUNT,
    Category.CABLE,
    Category.CONNECTOR,
    Category.HARDWARE,
    Category.BUMPER,
    Category.STORAGE,
    Category.COOLING,
}


def electrical_role(category: Category) -> ElectricalRole:
    if category in _SOURCES:
        return ElectricalRole.SOURCE
    if category in _PASSIVE:
        return ElectricalRole.PASSIVE
    return ElectricalRole.LOAD


class InterfaceKind(str, Enum):
    GPIO = "gpio"
    UART = "uart"
    I2C = "i2c"
    SPI = "spi"
    USB = "usb"
    PWM = "pwm"
    ETHERNET = "ethernet"
    WIFI = "wifi"


class InterfaceRole(str, Enum):
    HOST = "host"  # controller / master side
    PERIPHERAL = "peripheral"  # device / slave side


class InterfaceSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: InterfaceKind
    role: InterfaceRole
    logic_level_v: float | None = Field(default=None, gt=0)
    input_max_v: float | None = Field(default=None, gt=0)
    max_pin_current_a: float | None = Field(default=None, ge=0)
    i2c_address: int | None = Field(default=None, ge=0, le=127)


class ComponentOrigin(str, Enum):
    LIBRARY = "library"
    CUSTOM = "custom"


class ComponentStatus(str, Enum):
    VERIFIED = "verified"  # complete + source + human attestation
    CUSTOM = "custom"  # complete but not attested/sourced
    INCOMPLETE = "incomplete"  # required data missing


NUMERIC_SPEC_FIELDS: tuple[str, ...] = (
    "nominal_voltage_v",
    "min_voltage_v",
    "max_voltage_v",
    "nominal_current_a",
    "max_current_a",
    "power_w",
    "idle_current_a",
    "peak_current_a",
    "efficiency",
    "output_voltage_v",
    "output_max_current_a",
    "capacity_ah",
    "rated_torque_nm",
    "stall_torque_nm",
    "no_load_speed_rpm",
    "no_load_current_a",
    "stall_current_a",
    "temp_min_c",
    "temp_max_c",
    "mass_kg",
    "size_l_m",
    "size_w_m",
    "size_h_m",
)

_LOAD_REQUIRED = [
    "nominal_voltage_v",
    "min_voltage_v",
    "max_voltage_v",
    "nominal_current_a|power_w",
    "peak_current_a|max_current_a",
    "mass_kg",
]

_REQUIRED: dict[Category, list[str]] = {
    Category.BATTERY: ["nominal_voltage_v", "max_current_a", "capacity_ah", "mass_kg"],
    Category.DCDC_CONVERTER: [
        "min_voltage_v",
        "max_voltage_v",
        "output_voltage_v",
        "output_max_current_a",
        "efficiency",
        "mass_kg",
    ],
    Category.REGULATOR: [
        "min_voltage_v",
        "max_voltage_v",
        "output_voltage_v",
        "output_max_current_a",
        "efficiency",
        "mass_kg",
    ],
    Category.POWER_SUPPLY: ["output_voltage_v", "output_max_current_a", "mass_kg"],
    Category.MOTOR_DRIVER: ["min_voltage_v", "max_voltage_v", "max_current_a", "mass_kg"],
    Category.DC_MOTOR: [
        "nominal_voltage_v",
        "rated_torque_nm",
        "stall_torque_nm",
        "no_load_speed_rpm",
        "no_load_current_a",
        "stall_current_a",
        "mass_kg",
    ],
    Category.SERVO: [
        "nominal_voltage_v",
        "min_voltage_v",
        "max_voltage_v",
        "nominal_current_a",
        "stall_current_a",
        "mass_kg",
    ],
    Category.FUSE: ["max_current_a", "mass_kg"],
    Category.BMS: ["max_current_a", "mass_kg"],
    Category.SWITCH: ["max_current_a", "mass_kg"],
    Category.EMERGENCY_STOP: ["max_current_a", "mass_kg"],
    Category.WHEEL: ["mass_kg"],
    Category.CASTER: ["mass_kg"],
    Category.CHASSIS: ["mass_kg"],
    Category.MOUNT: ["mass_kg"],
    Category.CABLE: ["mass_kg"],
    Category.CONNECTOR: ["mass_kg"],
    Category.HARDWARE: ["mass_kg"],
    Category.BUMPER: ["mass_kg"],
    Category.STORAGE: ["mass_kg"],
    Category.COOLING: ["mass_kg"],
}


def required_fields(category: Category) -> list[str]:
    """Required spec fields; ``a|b`` means either field is acceptable."""
    return list(_REQUIRED.get(category, _LOAD_REQUIRED))


class ComponentSpec(BaseModel):
    """Structured datasheet. All technical numbers are optional (unknown = None)."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: Category
    origin: ComponentOrigin = ComponentOrigin.CUSTOM
    manufacturer: str | None = None
    part_number: str | None = None

    nominal_voltage_v: float | None = Field(default=None, gt=0)
    min_voltage_v: float | None = Field(default=None, ge=0)
    max_voltage_v: float | None = Field(default=None, gt=0)
    nominal_current_a: float | None = Field(default=None, ge=0)
    max_current_a: float | None = Field(default=None, ge=0)
    power_w: float | None = Field(default=None, ge=0)
    idle_current_a: float | None = Field(default=None, ge=0)
    peak_current_a: float | None = Field(default=None, ge=0)
    efficiency: float | None = Field(default=None, gt=0, le=1)

    output_voltage_v: float | None = Field(default=None, gt=0)
    output_max_current_a: float | None = Field(default=None, ge=0)
    capacity_ah: float | None = Field(default=None, gt=0)

    rated_torque_nm: float | None = Field(default=None, gt=0)
    stall_torque_nm: float | None = Field(default=None, gt=0)
    no_load_speed_rpm: float | None = Field(default=None, gt=0)
    no_load_current_a: float | None = Field(default=None, ge=0)
    stall_current_a: float | None = Field(default=None, ge=0)

    temp_min_c: float | None = None
    temp_max_c: float | None = None
    mass_kg: float | None = Field(default=None, ge=0)
    size_l_m: float | None = Field(default=None, gt=0)
    size_w_m: float | None = Field(default=None, gt=0)
    size_h_m: float | None = Field(default=None, gt=0)

    interfaces: list[InterfaceSpec] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    datasheet_version: str | None = None
    verified: bool = False
    notes: str | None = None

    @model_validator(mode="after")
    def _check_ranges(self) -> ComponentSpec:
        lo, hi = self.min_voltage_v, self.max_voltage_v
        if lo is not None and hi is not None and lo > hi:
            raise ValueError("min_voltage_v must be <= max_voltage_v")
        t_lo, t_hi = self.temp_min_c, self.temp_max_c
        if t_lo is not None and t_hi is not None and t_lo > t_hi:
            raise ValueError("temp_min_c must be <= temp_max_c")
        r, st = self.rated_torque_nm, self.stall_torque_nm
        if r is not None and st is not None and r > st:
            raise ValueError("rated_torque_nm must be <= stall_torque_nm")
        i_nom, i_max = self.nominal_current_a, self.max_current_a
        if i_nom is not None and i_max is not None and i_nom > i_max:
            raise ValueError("nominal_current_a must be <= max_current_a")
        return self

    @property
    def role(self) -> ElectricalRole:
        return electrical_role(self.category)

    def missing_required(self) -> list[str]:
        missing: list[str] = []
        for req in required_fields(self.category):
            options = req.split("|")
            if all(getattr(self, o) is None for o in options):
                missing.append(req)
        return missing

    @property
    def status(self) -> ComponentStatus:
        if self.missing_required():
            return ComponentStatus.INCOMPLETE
        if self.verified and self.sources:
            return ComponentStatus.VERIFIED
        return ComponentStatus.CUSTOM
