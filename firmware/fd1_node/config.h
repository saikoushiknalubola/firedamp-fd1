// FD-1 routing and safety parameters. Defaults follow UNECE Best Practice Guidance
// (2nd ed., 2016): methane explosive at ~5-15 % in air; good-practice minimum for
// transport and use is >= 30 % (2 x upper explosive limit); national minimums 25-40 %.
// Every value here is a site setting and must be agreed with the mine's safety officer.
#pragma once

#define CH4_ROUTE_MIN_PCT        30.0f   // >= this: gas may be routed to utilisation/destruction
#define CH4_ROUTE_HYST_PCT        1.0f   // leave THROTTLE only above ROUTE_MIN + HYST
#define CH4_ISOLATE_PCT          25.0f   // below this: isolate borehole (latched)
#define O2_ISOLATE_PCT           10.0f   // above this: isolate regardless of CH4
#define PLAUSIBILITY_PTS          5.0f   // max |NDIR CH4 - O2-derived CH4| before FAULT
#define THROTTLE_RECOVERY_S        120   // time allowed to recover purity before isolating
#define NDIR_WARMUP_S              180   // MH-440D warm-up (datasheet: 3 min)
#define SENSOR_TIMEOUT_MS         3000

// Orifice meter (bench rig): 3.4 mm bore in 15.8 mm line, beta 0.215
#define ORIFICE_BORE_M         0.0034f
#define PIPE_ID_M              0.0158f
#define ORIFICE_CD             0.60f     // replaced by rig calibration value
#define RHO_AIR_20C            1.204f    // kg/m3
#define RHO_CH4_20C            0.668f
#define RHO_CO2_20C            1.842f    // bench surrogate mode
#define O2_IN_AIR_PCT          20.95f

#define MODBUS_ADDR               1      // node #1; node #2 = 2
#define MODBUS_BAUD           19200
