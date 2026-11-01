"""Versioned project data model.

Coordinates: origin on the ground below the chassis centre; x forward, y left,
z up (metres). All values SI. Unknown = None.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.component import InterfaceKind

CURRENT_SCHEMA_VERSION = 1


class Vec3(BaseModel):
    model_config = ConfigDict(extra="forbid")
    x: float
    y: float
    z: float


class ProjectInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    author: str = ""
    robot_type: str = "differential"
    version_label: str = "0.1"


class ComponentInstance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    quantity: int = Field(default=1, ge=1)
    position: Vec3 | None = None
    # Fraction of time the load is active (0..1). 1.0 = continuous (conservative).
    duty_cycle: float = Field(default=1.0, ge=0, le=1)


class Rail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    voltage_v: float | None = Field(default=None, gt=0)
    source_instance_id: str | None = None


class PowerLink(BaseModel):
    model_config = ConfigDict(extra="forbid")
    load_instance_id: str
    rail_id: str


class GroundNet(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    instance_ids: list[str] = Field(default_factory=list)


class SignalLink(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    host_instance_id: str
    peripheral_instance_id: str
    interface: InterfaceKind
    bus: str | None = None  # e.g. "i2c-1": peripherals on one bus share addresses
    level_shifter: bool = False


class CableRun(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    rail_id: str
    # Load carried by the run; None = the whole rail current (feeder cable).
    load_instance_id: str | None = None
    length_m: float = Field(gt=0)  # one-way length
    section_mm2: float | None = Field(default=None, gt=0)


class ElectricalConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rails: list[Rail] = Field(default_factory=list)
    power_links: list[PowerLink] = Field(default_factory=list)
    ground_nets: list[GroundNet] = Field(default_factory=list)
    signal_links: list[SignalLink] = Field(default_factory=list)
    cables: list[CableRun] = Field(default_factory=list)


class Chassis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    length_m: float | None = Field(default=None, gt=0)
    width_m: float | None = Field(default=None, gt=0)
    height_m: float | None = Field(default=None, gt=0)
    mass_kg: float | None = Field(default=None, ge=0)
    cog: Vec3 | None = None  # chassis own centre of gravity


class WheelKind(str, Enum):
    DRIVE = "drive"
    CASTER = "caster"


class Wheel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    kind: WheelKind
    x_m: float
    y_m: float
    radius_m: float = Field(gt=0)
    mass_kg: float | None = Field(default=None, ge=0)


class MechanicalConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chassis: Chassis = Field(default_factory=Chassis)
    wheels: list[Wheel] = Field(default_factory=list)


class BatteryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    instance_id: str | None = None
    technology: str | None = None
    cells_series: int | None = Field(default=None, ge=1)
    strings_parallel: int | None = Field(default=None, ge=1)
    cell_capacity_ah: float | None = Field(default=None, gt=0)
    cell_nominal_v: float | None = Field(default=None, gt=0)
    cell_max_v: float | None = Field(default=None, gt=0)
    cell_min_v: float | None = Field(default=None, gt=0)
    max_discharge_current_a: float | None = Field(default=None, gt=0)
    usable_fraction: float | None = Field(default=None, gt=0, le=1)
    discharge_efficiency: float | None = Field(default=None, gt=0, le=1)
    target_runtime_h: float | None = Field(default=None, gt=0)
    measured_runtime_h: float | None = Field(default=None, gt=0)


class MotorizationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    motor_instance_id: str | None = None
    driver_instance_id: str | None = None
    motor_count: int | None = Field(default=None, ge=1)
    wheel_radius_m: float | None = Field(default=None, gt=0)
    target_speed_m_s: float | None = Field(default=None, gt=0)
    acceleration_m_s2: float | None = Field(default=None, ge=0)
    max_slope_deg: float | None = Field(default=None, ge=0, lt=90)
    rolling_resistance_coeff: float | None = Field(default=None, ge=0)
    gear_ratio: float = Field(default=1.0, gt=0)  # extra reduction after the gearmotor output
    transmission_efficiency: float | None = Field(default=None, gt=0, le=1)


class AnalysisSettings(BaseModel):
    """Engineering conventions (user-editable, not component data)."""

    model_config = ConfigDict(extra="forbid")
    margin_limit_fraction: float = Field(default=0.8, gt=0, le=1)
    max_voltage_drop_fraction: float = Field(default=0.05, gt=0, lt=1)
    ambient_temp_c: float | None = None


class Point(BaseModel):
    model_config = ConfigDict(extra="forbid")
    x: float
    y: float


class Polygon(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    points: list[Point] = Field(min_length=3)


class VisitorSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    radius_m: float = Field(gt=0)
    speed_m_s: float = Field(gt=0)
    waypoints: list[Point] = Field(min_length=1)
    loop: bool = False


class LidarSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ray_count: int = Field(ge=1, le=3600)
    fov_deg: float = Field(gt=0, le=360)
    max_range_m: float = Field(gt=0)
    noise_sigma_m: float = Field(default=0.0, ge=0)


class SimulationScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")
    world_width_m: float = Field(default=10.0, gt=0)
    world_height_m: float = Field(default=10.0, gt=0)
    grid_m: float = Field(default=0.5, gt=0)
    obstacles: list[Polygon] = Field(default_factory=list)
    forbidden_zones: list[Polygon] = Field(default_factory=list)
    visitors: list[VisitorSpec] = Field(default_factory=list)
    lidar: LidarSpec | None = None
    start: Point = Field(default_factory=lambda: Point(x=1.0, y=1.0))
    start_heading_rad: float = 0.0
    waypoints: list[Point] = Field(default_factory=list)
    dt_s: float = Field(default=0.02, gt=0, le=0.1)
    duration_s: float = Field(default=30.0, gt=0, le=3600)
    seed: int = 0
    stop_distance_m: float | None = Field(default=None, gt=0)
    lidar_every_n_steps: int = Field(default=25, ge=1)


class ProjectData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: int = CURRENT_SCHEMA_VERSION
    info: ProjectInfo
    components: list[ComponentInstance] = Field(default_factory=list)
    mechanical: MechanicalConfig = Field(default_factory=MechanicalConfig)
    electrical: ElectricalConfig = Field(default_factory=ElectricalConfig)
    battery: BatteryConfig = Field(default_factory=BatteryConfig)
    motorization: MotorizationConfig = Field(default_factory=MotorizationConfig)
    settings: AnalysisSettings = Field(default_factory=AnalysisSettings)
    simulation: SimulationScenario = Field(default_factory=SimulationScenario)
    results: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_references(self) -> ProjectData:
        ids = [c.id for c in self.components]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate component instance ids")
        known = set(ids)
        e = self.electrical
        rail_ids = [r.id for r in e.rails]
        if len(rail_ids) != len(set(rail_ids)):
            raise ValueError("duplicate rail ids")
        for r in e.rails:
            if r.source_instance_id is not None and r.source_instance_id not in known:
                raise ValueError(f"rail {r.id}: unknown source instance {r.source_instance_id}")
        for pl in e.power_links:
            if pl.load_instance_id not in known:
                raise ValueError(f"power link: unknown instance {pl.load_instance_id}")
            if pl.rail_id not in rail_ids:
                raise ValueError(f"power link: unknown rail {pl.rail_id}")
        for g in e.ground_nets:
            for i in g.instance_ids:
                if i not in known:
                    raise ValueError(f"ground net {g.id}: unknown instance {i}")
        for s in e.signal_links:
            for i in (s.host_instance_id, s.peripheral_instance_id):
                if i not in known:
                    raise ValueError(f"signal link {s.id}: unknown instance {i}")
        for c in e.cables:
            if c.rail_id not in rail_ids:
                raise ValueError(f"cable {c.id}: unknown rail {c.rail_id}")
            if c.load_instance_id is not None and c.load_instance_id not in known:
                raise ValueError(f"cable {c.id}: unknown instance {c.load_instance_id}")
        for ref in (
            self.battery.instance_id,
            self.motorization.motor_instance_id,
            self.motorization.driver_instance_id,
        ):
            if ref is not None and ref not in known:
                raise ValueError(f"unknown instance reference {ref}")
        return self
