import itertools
import numpy as np
import pytest
from pytest import approx

import cantera as ct


@pytest.fixture(scope='function')
def water(request):
    request.cls.water = ct.Water()

@pytest.mark.usefixtures("water")
class TestPureFluid:
    """ Test functionality of the PureFluid class """

    def test_critical_properties(self):
        assert self.water.critical_pressure == approx(22.089e6)
        assert self.water.critical_temperature == approx(647.286)
        assert self.water.critical_density == approx(317.0)

    def test_temperature_limits(self):
        co2 = ct.CarbonDioxide()
        assert co2.min_temp == approx(216.54)
        assert co2.max_temp == approx(1500.0)

    def test_set_state(self):
        self.water.PQ = 101325, 0.5
        assert self.water.P == approx(101325)
        assert self.water.Q == approx(0.5)

        self.water.TQ = 500, 0.8
        assert self.water.T == approx(500)
        assert self.water.Q == approx(0.8)

    def test_substance_set(self):
        self.water.TV = 400, 1.45
        assert self.water.T == approx(400)
        assert self.water.v == approx(1.45)
        with pytest.raises(ct.CanteraError, match='Negative specific volume'):
            self.water.TV = 300, -1.

        self.water.PV = 101325, 1.45
        assert self.water.P == approx(101325)
        assert self.water.v == approx(1.45)

        self.water.UP = -1.45e7, 101325
        assert self.water.u == approx(-1.45e7)
        assert self.water.P == approx(101325)

        self.water.VH = 1.45, -1.45e7
        assert self.water.v == approx(1.45)
        assert self.water.h == approx(-1.45e7)

        self.water.TH = 400, -1.45e7
        assert self.water.T == approx(400)
        assert self.water.h == approx(-1.45e7)

        self.water.SH = 5000, -1.45e7
        assert self.water.s == approx(5000)
        assert self.water.h == approx(-1.45e7)

        self.water.ST = 5000, 400
        assert self.water.s == approx(5000)
        assert self.water.T == approx(400)

    def test_states(self):
        assert self.water._native_state == ('T', 'D')
        assert 'TPY' not in self.water._full_states.values()
        assert 'TQ' in self.water._partial_states.values()

    def test_set_Q(self):
        self.water.TQ = 500, 0.0
        p = self.water.P
        self.water.Q = 0.8
        assert self.water.P == approx(p)
        assert self.water.T == approx(500)
        assert self.water.Q == approx(0.8)

        self.water.TP = 650, 101325
        with pytest.raises(ct.CanteraError):
            self.water.Q = 0.1

        self.water.TP = 300, 101325
        with pytest.raises(ValueError):
            self.water.Q = 0.3

    def test_set_minmax(self):
        self.water.TP = self.water.min_temp, 101325
        assert self.water.T == approx(self.water.min_temp)

        self.water.TP = self.water.max_temp, 101325
        assert self.water.T == approx(self.water.max_temp)

    def check_fd_properties(self, T1, P1, T2, P2, tol):
        # Properties which are computed as finite differences
        self.water.TP = T1, P1
        h1a = self.water.enthalpy_mass
        cp1 = self.water.cp_mass
        cv1 = self.water.cv_mass
        k1 = self.water.isothermal_compressibility
        alpha1 = self.water.thermal_expansion_coeff
        h1b = self.water.enthalpy_mass

        self.water.TP = T2, P2
        h2a = self.water.enthalpy_mass
        cp2 = self.water.cp_mass
        cv2 = self.water.cv_mass
        k2 = self.water.isothermal_compressibility
        alpha2 = self.water.thermal_expansion_coeff
        h2b = self.water.enthalpy_mass

        assert cp1 == approx(cp2, rel=tol)
        assert cv1 == approx(cv2, rel=tol)
        assert k1 == approx(k2, rel=tol)
        assert alpha1 == approx(alpha2, rel=tol)

        # calculating these finite difference properties should not perturb the
        # state of the object (except for checks on edge cases)
        assert h1a == approx(h1b, rel=1e-9)
        assert h2a == approx(h2b, rel=1e-9)

    def test_properties_near_min(self):
        self.check_fd_properties(self.water.min_temp*(1+1e-5), 101325,
                                 self.water.min_temp*(1+1e-4), 101325, 1e-2)

    def test_properties_near_max(self):
        self.check_fd_properties(self.water.max_temp*(1-1e-5), 101325,
                                 self.water.max_temp*(1-1e-4), 101325, 1e-2)

    def test_properties_near_sat1(self):
        for T in [340,390,420]:
            self.water.TQ = T, 0.0
            P = self.water.P
            self.check_fd_properties(T, P+0.01, T, P+0.5, 1e-4)

    def test_properties_near_sat2(self):
        for T in [340,390,420]:
            self.water.TQ = T, 0.0
            P = self.water.P
            self.check_fd_properties(T, P-0.01, T, P-0.5, 1e-4)

    def test_isothermal_compressibility_lowP(self):
        # Low-pressure limit corresponds to ideal gas
        ref = ct.Solution('h2o2.yaml', transport_model=None)
        ref.TPX = 450, 12, 'H2O:1.0'
        self.water.TP = 450, 12
        assert ref.isothermal_compressibility == approx(
               self.water.isothermal_compressibility, rel=1e-5)

    def test_thermal_expansion_coeff_lowP(self):
        # Low-pressure limit corresponds to ideal gas
        ref = ct.Solution('h2o2.yaml', transport_model=None)
        ref.TPX = 450, 12, 'H2O:1.0'
        self.water.TP = 450, 12
        assert ref.thermal_expansion_coeff == approx(
               self.water.thermal_expansion_coeff, rel=1e-5)

    def test_thermal_expansion_coeff_TD(self):
        for T in [440, 550, 660]:
            self.water.TD = T, 0.1
            assert T * self.water.thermal_expansion_coeff == approx(1.0, rel=1e-2)

    def test_pq_setter_triple_check(self):
        self.water.PQ = 101325, .2
        T = self.water.T
        # change T such that it would result in a Psat larger than P
        self.water.TP = 400, 101325
        # ensure that correct triple point pressure is recalculated
        # (necessary as this value is not stored by the C++ base class)
        self.water.PQ = 101325, .2
        assert T == approx(self.water.T, rel=1e-9)
        with pytest.raises(ct.CanteraError, match='below triple point'):
            # min_temp is triple point temperature
            self.water.TP = self.water.min_temp, 101325
            P = self.water.P_sat # triple-point pressure
            self.water.PQ = .999*P, .2

    def test_quality_exceptions(self):
        # Critical point
        self.water.TP = 300, ct.one_atm
        self.water.TQ = self.water.critical_temperature, .5
        assert self.water.P == approx(self.water.critical_pressure)
        self.water.TP = 300, ct.one_atm
        self.water.PQ = self.water.critical_pressure, .5
        assert self.water.T == approx(self.water.critical_temperature)

        # Supercritical
        with pytest.raises(ct.CanteraError, match='supercritical'):
            self.water.TQ = 1.001 * self.water.critical_temperature, 0.
        with pytest.raises(ct.CanteraError, match='supercritical'):
            self.water.PQ = 1.001 * self.water.critical_pressure, 0.

        # Q negative
        with pytest.raises(ct.CanteraError, match='Invalid vapor fraction'):
            self.water.TQ = 373.15, -.001
        with pytest.raises(ct.CanteraError, match='Invalid vapor fraction'):
            self.water.PQ = ct.one_atm, -.001

        # Q larger than one
        with pytest.raises(ct.CanteraError, match='Invalid vapor fraction'):
            self.water.TQ = 373.15, 1.001
        with pytest.raises(ct.CanteraError, match='Invalid vapor fraction'):
            self.water.PQ = ct.one_atm, 1.001

    def test_saturated_mixture(self):
        self.water.TP = 300, ct.one_atm
        with pytest.raises(ct.CanteraError, match='Saturated mixture detected'):
            self.water.TP = 300, self.water.P_sat

        w = ct.Water()

        # Saturated vapor
        self.water.TQ = 373.15, 1.
        assert self.water.phase_of_matter == 'liquid-gas-mix'
        w.TP = self.water.T, .999 * self.water.P_sat
        assert self.water.cp == approx(w.cp, rel=1.e-3)
        assert self.water.cv == approx(w.cv, rel=1.e-3)
        assert self.water.thermal_expansion_coeff == approx(w.thermal_expansion_coeff, rel=1.e-3)
        assert self.water.isothermal_compressibility == approx(w.isothermal_compressibility, rel=1.e-3)

        # Saturated mixture
        self.water.TQ = 373.15, .5
        assert self.water.phase_of_matter == 'liquid-gas-mix'
        assert self.water.cp == np.inf
        assert np.isnan(self.water.cv)
        assert self.water.isothermal_compressibility == np.inf
        assert self.water.thermal_expansion_coeff == np.inf

        # Saturated liquid
        self.water.TQ = 373.15, 0.
        assert self.water.phase_of_matter == 'liquid-gas-mix'
        w.TP = self.water.T, 1.001 * self.water.P_sat
        assert self.water.cp == approx(w.cp, rel=1.e-3)
        assert self.water.cv == approx(w.cv, rel=1.e-3)
        assert self.water.thermal_expansion_coeff == approx(w.thermal_expansion_coeff, rel=1.e-3)
        assert self.water.isothermal_compressibility == approx(w.isothermal_compressibility, rel=1.e-3)

    def test_saturation_near_limits(self):
        # Low temperature limit (triple point)
        self.water.TP = 300, ct.one_atm
        self.water.P_sat # ensure that solver buffers sufficiently different values
        self.water.TP = self.water.min_temp, ct.one_atm
        psat = self.water.P_sat
        self.water.TP = 300, ct.one_atm
        self.water.P_sat # ensure that solver buffers sufficiently different values
        self.water.TP = 300, psat
        assert self.water.T_sat == approx(self.water.min_temp)

        # High temperature limit (critical point) - saturation temperature
        self.water.TP = 300, ct.one_atm
        self.water.P_sat # ensure that solver buffers sufficiently different values
        self.water.TP = self.water.critical_temperature, self.water.critical_pressure
        assert self.water.T_sat == approx(self.water.critical_temperature)

        # High temperature limit (critical point) - saturation pressure
        self.water.TP = 300, ct.one_atm
        self.water.P_sat # ensure that solver buffers sufficiently different values
        self.water.TP = self.water.critical_temperature, self.water.critical_pressure
        assert self.water.P_sat == approx(self.water.critical_pressure)

        # Supercricital
        with pytest.raises(ct.CanteraError, match='Illegal temperature value'):
            self.water.TP = 1.001 * self.water.critical_temperature, self.water.critical_pressure
            self.water.P_sat
        with pytest.raises(ct.CanteraError, match='Illegal pressure value'):
            self.water.TP = self.water.critical_temperature, 1.001 * self.water.critical_pressure
            self.water.T_sat

        # Below triple point
        with pytest.raises(ct.CanteraError, match='Illegal temperature'):
            self.water.TP = .999 * self.water.min_temp, ct.one_atm
            self.water.P_sat
        # @todo: test disabled pending fix of GitHub issue #605
        # with pytest.raises(ct.CanteraError, match='Illegal pressure value'):
        #     self.water.TP = 300, .999 * psat
        #     self.water.T_sat

    def test_TPQ(self):
        self.water.TQ = 400, 0.8
        T, P, Q = self.water.TPQ
        assert T == approx(400)
        assert Q == approx(0.8)

        # a supercritical state
        self.water.TPQ = 800, 3e7, 1
        assert self.water.T == approx(800)
        assert self.water.P == approx(3e7)

        self.water.TPQ = T, P, Q
        assert self.water.Q == approx(0.8)
        with pytest.raises(ct.CanteraError, match='inconsistent'):
            self.water.TPQ = T, .999*P, Q
        with pytest.raises(ct.CanteraError, match='inconsistent'):
            self.water.TPQ = T, 1.001*P, Q
        with pytest.raises(TypeError):
            self.water.TPQ = T, P, 'spam'

        self.water.TPQ = 500, 1e5, 1  # superheated steam
        assert self.water.P == approx(1e5)
        with pytest.raises(ct.CanteraError, match='inconsistent'):
            self.water.TPQ = 500, 1e5, 0  # vapor fraction should be 1 (T < Tc)
        with pytest.raises(ct.CanteraError, match='inconsistent'):
            self.water.TPQ = 700, 1e5, 0  # vapor fraction should be 1 (T > Tc)

    def test_phase_of_matter(self):
        self.water.TP = 300, 101325
        assert self.water.phase_of_matter == "liquid"
        self.water.TP = 500, 101325
        assert self.water.phase_of_matter == "gas"
        self.water.TP = self.water.critical_temperature*2, 101325
        assert self.water.phase_of_matter == "supercritical"
        self.water.TP = 300, self.water.critical_pressure*2
        assert self.water.phase_of_matter == "supercritical"
        self.water.TQ = 300, 0.4
        assert self.water.phase_of_matter == "liquid-gas-mix"

        # These cases work after fixing GH-786
        n2 = ct.Nitrogen()
        n2.TP = 100, 1000
        assert n2.phase_of_matter == "gas"

        co2 = ct.CarbonDioxide()
        assert co2.phase_of_matter == "gas"

    def test_water_backends(self):
        w = ct.Water(backend='Reynolds')
        assert w.thermo_model == 'pure-fluid'
        w = ct.Water(backend='IAPWS95')
        assert w.thermo_model == 'liquid-water-IAPWS95'
        with pytest.raises(KeyError, match='Unknown backend'):
            ct.Water('foobar')

    def test_water_iapws(self):
        w = ct.Water(backend='IAPWS95')
        assert w.critical_density == approx(322.)
        assert w.critical_temperature == approx(647.096)
        assert w.critical_pressure == approx(22064000.0)

        # test internal TP setters (setters update temperature at constant
        # density before updating pressure)
        w.TP = 300, ct.one_atm
        dens = w.density
        w.TP = 2000, ct.one_atm # supercritical
        assert w.phase_of_matter == "supercritical"
        w.TP = 300, ct.one_atm # state goes from supercritical -> gas -> liquid
        assert w.density == approx(dens)
        assert w.phase_of_matter == "liquid"

        # test setters for critical conditions
        w.TP = w.critical_temperature, w.critical_pressure
        assert w.density == approx(322.)
        w.TP = 2000, ct.one_atm # uses current density as initial guess
        w.TP = 273.16, ct.one_atm # uses fixed density as initial guess
        assert w.density == approx(999.84376)
        assert w.phase_of_matter == "liquid"
        w.TP = w.T, w.P_sat
        assert w.phase_of_matter == "liquid"
        with pytest.raises(ct.CanteraError, match="assumes liquid phase"):
            w.TP = 273.1599999, ct.one_atm
        with pytest.raises(ct.CanteraError, match="assumes liquid phase"):
            w.TP = 500, ct.one_atm


# To minimize errors when transcribing tabulated data, the input units here are:
# T: K, P: MPa, rho: kg/m3, v: m3/kg, (u,h): kJ/kg, s: kJ/kg-K
# Which are then converted to SI
class StateData:
    def __init__(self, phase, T, p, rho=None, v=None, u=None, h=None, s=None, relax=False):
        self.phase = phase
        self.T = T
        self.p = p * 1e6
        self.rho = rho if rho else 1.0/v
        self.u = 1e3 * u if u is not None else 1e3 * h - self.p/self.rho
        self.s = 1e3 * s
        self.tolMod = 10.0 if relax else 1.0


class Tolerances:
    def __init__(self, p=None, u=None, s=None,
                 dUdS=None, dAdV=None, dPdT=None, hTs=None):
        self.p = p or 2e-5
        self.u = u or 2e-6
        self.s = s or 2e-6
        self.dUdS = dUdS or 2e-6
        self.dAdV = dAdV or 2e-6
        self.dPdT = dPdT or 2e-4
        self.hTs = hTs or 2e-4


@pytest.fixture(scope='class')
def setup_fluid(request):
    """Fixture to set up fluid, refState, and initial internal energy/entropy."""
    if request.cls.name not in request.cls.fluids:
        request.cls.fluids[request.cls.name] = ct.PureFluid("liquidvapor.yaml", request.cls.name)
    request.cls.fluid = request.cls.fluids[request.cls.name]
    request.cls.fluid.TD = request.cls.refState.T, request.cls.refState.rho
    request.cls.u0 = request.cls.fluid.u
    request.cls.s0 = request.cls.fluid.s


@pytest.mark.usefixtures("setup_fluid")
class PureFluidTestCases:
    """
    Test the results of pure fluid phase calculations against tabulated
    references and for consistency with basic thermodynamic relations.
    """
    fluids = {}
    states = []
    refState = None
    tol = Tolerances()

    def a(self, T, rho):
        """ Helmholtz free energy """
        self.fluid.TD = T, rho
        return self.fluid.u - T * self.fluid.s

    def test_has_phase_transition(self):
        assert self.fluid.has_phase_transition

    def test_consistency_temperature(self):
        for state in self.states:
            dT = 2e-5 * state.T
            self.fluid.TD = state.T-dT, state.rho
            s1 = self.fluid.s
            u1 = self.fluid.u
            self.fluid.TD = state.T+dT, state.rho
            s2 = self.fluid.s
            u2 = self.fluid.u

            # At constant volume, dU = T dS
            msg = 'At state: T=%s, rho=%s' % (state.T, state.rho)
            assert (u2-u1)/(s2-s1) == approx(state.T, rel=self.tol.dUdS), msg

    def test_consistency_volume(self):
        for state in self.states:
            self.fluid.TD = state.T, state.rho
            p = self.fluid.P
            V = 1 / state.rho
            dV = 5e-6 * V

            a1 = self.a(state.T, 1/(V-0.5*dV))
            a2 = self.a(state.T, 1/(V+0.5*dV))

            # dP/drho is high for liquids, so relax tolerances
            tol = 300*self.tol.dAdV if state.phase == 'liquid' else self.tol.dAdV

            # At constant temperature, dA = - p dV
            msg = 'At state: T=%s, rho=%s' % (state.T, state.rho)
            assert -(a2-a1)/dV == approx(p, rel=tol), msg

    def test_saturation(self):
        for state in self.states:
            if state.phase == 'super':
                continue

            dT = 1e-6 * state.T
            self.fluid.TQ = state.T, 0
            p1 = self.fluid.P
            vf = 1.0 / self.fluid.density
            hf = self.fluid.h
            sf = self.fluid.s

            self.fluid.TQ = state.T + dT, 0
            p2 = self.fluid.P

            self.fluid.TQ = state.T, 1
            vg = 1.0 / self.fluid.density
            hg = self.fluid.h
            sg = self.fluid.s

            # Clausius-Clapeyron Relation
            msg = 'At state: T=%s, rho=%s' % (state.T, state.rho)
            assert (p2-p1)/dT == approx((hg-hf)/(state.T * (vg-vf)),
                   rel=self.tol.dPdT), msg

            # True for a change in state at constant pressure and temperature
            assert hg-hf == approx(state.T * (sg-sf), rel=self.tol.hTs)

    def test_pressure(self):
        for state in self.states:
            self.fluid.TD = state.T, state.rho
            # dP/drho is high for liquids, so relax tolerances
            tol = 70*self.tol.p if state.phase == 'liquid' else self.tol.p
            tol *= state.tolMod
            msg = 'At state: T=%s, rho=%s' % (state.T, state.rho)
            assert self.fluid.P == approx(state.p, rel=tol), msg

    def test_internal_energy(self):
        for state in self.states:
            self.fluid.TD = state.T, state.rho
            msg = 'At state: T=%s, rho=%s' % (state.T, state.rho)
            assert self.fluid.u - self.u0 == approx(state.u - self.refState.u,
                   rel=self.tol.u * state.tolMod), msg

    def test_entropy(self):
        for state in self.states:
            self.fluid.TD = state.T, state.rho
            msg = 'At state: T=%s, rho=%s' % (state.T, state.rho)
            assert self.fluid.s - self.s0 == approx(state.s - self.refState.s,
                   rel=self.tol.s * state.tolMod), msg


class TestHFC134a(PureFluidTestCases):
    """
    Reference values for HFC134a taken from NIST Chemistry WebBook, which
    implements the same EOS from Tillner-Roth and Baehr as Cantera, so close
    agreement is expected.
    """
    states = [
        StateData('liquid', 175.0, 0.1, rho=1577.6239, u=77.534586, s=0.44788182),
        StateData('liquid', 210.0, 0.1, rho=1483.2128, u=119.48566, s=0.66633877),
        StateData('vapor', 250.0, 0.1, rho=5.1144317, u=365.59424, s=1.7577491),
        StateData('vapor', 370.0, 0.1, rho=3.3472612, u=459.82664, s=2.0970769),
        StateData('liquid', 290.0, 10, rho=1278.4700, u=216.99119, s=1.0613409),
        StateData('super', 410.0, 10, rho=736.54666, u=399.02258, s=1.5972395),
        StateData('super', 450.0, 40, rho=999.34087, u=411.92422, s=1.6108568)]

    refState = StateData('critical', 374.21, 4.05928, rho=511.900, u=381.70937, s=1.5620991)
    name = "HFC-134a"



# Reference values for the following substances are taken from the tables in
# W.C. Reynolds, "Thermodynamic Properties in SI", which is the source of
# Cantera's equations of state for these substances. Agreement is limited by
# the precision of the results printed in the book (typically 4 significant
# figures).

# Property comparisons for saturated states are further limited by the use of
# different methods for satisfying the phase equilibrium condition g_l = g_v.
# Cantera uses the actual equation of state, while the tabulated values given
# by Reynolds are based on the given P_sat(T_sat) relations.
class TestCarbonDioxide(PureFluidTestCases):
    states = [
        StateData('liquid', 230.0, 2.0, rho=1132.4, h=28.25, s=0.1208),
        StateData('liquid', 270.0, 10.0, rho=989.97, h=110.59, s=0.4208),
        StateData('vapor', 250.0, 1.788, v=0.02140, h=358.59, s=1.4500, relax=True),  # sat
        StateData('vapor', 300.0, 2.0, v=0.02535, h=409.41, s=1.6174),
        StateData('super', 500.0, 1.0, v=0.09376, h=613.22, s=2.2649),
        StateData('super', 600.0, 20.0, v=0.00554, h=681.94, s=1.8366)]

    refState = StateData('critical', 304.21, 7.3834, rho=464.0, h=257.31, s=0.9312)
    name = "carbon-dioxide"
    tol = Tolerances(2e-3, 2e-3, 2e-3)


class TestHeptane(PureFluidTestCases):
    states = [
        StateData('liquid', 300.0, 0.006637, v=0.001476, h=0.0, s=0.0, relax=True),  # sat
        StateData('liquid', 400.0, 0.2175, v=0.001712, h=248.01, s=0.709, relax=True),  # sat
        StateData('vapor', 490.0, 1.282, v=0.02222, h=715.64, s=1.7137, relax=True),  # sat
        StateData('vapor', 480.0, 0.70, v=0.04820, h=713.04, s=1.7477),
        StateData('super', 600.0, 2.0, v=0.01992, h=1014.87, s=2.2356),
        StateData('super', 680.0, 0.2, v=0.2790, h=1289.29, s=2.8450)]

    refState = StateData('critical', 537.68, 2.6199, rho=197.60, h=747.84, s=1.7456)
    name = "heptane"
    tol = Tolerances(2e-3, 2e-3, 2e-3)


# para-hydrogen
class TestHydrogen(PureFluidTestCases):
    states = [
        StateData('liquid', 18.0, 0.04807, v=0.013660, h=30.1, s=1.856, relax=True),  # sat
        StateData('liquid', 26.0, 0.4029, v=0.015911, h=121.2, s=5.740, relax=True),  # sat
        StateData('vapor', 30.0, 0.8214, v=0.09207, h=487.4, s=17.859, relax=True),  # sat
        StateData('super', 100.0, 0.20, v=2.061, h=1398.3, s=39.869),
        StateData('super', 200.0, 20.0, v=0.04795, h=3015.9, s=31.274),
        StateData('super', 300.0, 0.50, v=2.482, h=4511.6, s=53.143),
        StateData('super', 600.0, 1.00, v=2.483, h=8888.4, s=60.398),
        StateData('super', 800.0, 4.0, v=0.8329, h=11840.0, s=58.890)]

    refState = StateData('critical', 32.938, 1.2838, rho=31.36, h=346.5, s=12.536)
    name = "hydrogen"
    tol = Tolerances(2e-3, 2e-3, 2e-3, 2e-4)

class TestMethane(PureFluidTestCases):
    states = [
        StateData('liquid', 100.0, 0.50, rho=439.39, h=31.65, s=0.3206),
        StateData('liquid', 140.0, 2.0, rho=379.51, h=175.48, s=1.4963),
        StateData('vapor', 150.0, 0.20, v=0.3772, h=660.72, s=5.5435),
        StateData('vapor', 160.0, 1.594, v=0.03932, h=627.96, s=4.3648, relax=True),  # sat
        StateData('vapor', 175.0, 1.0, v=0.08157, h=692.55, s=4.9558),
        StateData('super', 200.0, 0.2, v=0.5117, h=767.37, s=6.1574),
        StateData('super', 300.0, 0.5, v=0.3083, h=980.87, s=6.5513)]

    refState = StateData('critical', 190.555, 4.5988, rho=160.43, h=490.61, s=3.2853)
    name = "methane"
    tol = Tolerances(2e-3, 2e-3, 2e-3)

class TestNitrogen(PureFluidTestCases):
    states = [
        StateData('liquid', 80.0, 0.1370, v=0.001256, h=33.50, s=0.4668, relax=True),  # sat
        StateData('vapor', 110.0, 1.467, v=0.01602, h=236.28, s=2.3896, relax=True),  # sat
        StateData('super', 200.0, 0.5, v=0.1174, h=355.05, s=3.5019),
        StateData('super', 300.0, 10.0, v=0.00895, h=441.78, s=2.9797),
        StateData('super', 500.0, 5.0, v=0.03031, h=668.48, s=3.7722),
        StateData('super', 600.0, 100.0, v=0.00276, h=827.54, s=3.0208)]

    refState = StateData('critical', 126.200, 3.400, rho=314.03, h=180.78, s=1.7903)
    name = "nitrogen"
    tol = Tolerances(2e-3, 2e-3, 2e-3)

class TestOxygen(PureFluidTestCases):
    states = [
        StateData('liquid', 80.0, 0.03009, v=0.000840, h=42.56, s=0.6405, relax=True),  # sat
        StateData('liquid', 125.0, 1.351, v=0.001064, h=123.24, s=1.4236, relax=True),  # sat
        StateData('vapor', 145.0, 3.448, v=0.006458, h=276.45, s=2.4852, relax=True),  # sat
        StateData('super', 200.0, 0.050, v=1.038, h=374.65, s=4.1275),
        StateData('super', 300.0, 1.0, v=0.07749, h=463.76, s=3.7135),
        StateData('super', 600.0, 0.20, v=0.7798, h=753.38, s=4.7982),
        StateData('super', 800.0, 5.0, v=0.04204, h=961.00, s=4.2571)]

    refState = StateData('critical', 154.581, 5.0429, rho=436.15, h=226.53, s=2.1080)
    name = "oxygen"
    tol = Tolerances(2e-3, 2e-3, 2e-3)

class TestWater(PureFluidTestCases):
    states = [
        StateData('liquid', 295.0, 0.002620, v=0.0010025, h=90.7, s=0.3193, relax=True),
        StateData('vapor', 315.0, 0.008143, v=17.80, h=2577.1, s=8.2216, relax=True),
        StateData('liquid', 440.0, 0.7332, v=0.001110, h=705.0, s=2.0096, relax=True),
        StateData('vapor', 510.0, 3.163, v=0.06323, h=2803.6, s=6.1652, relax=True),
        StateData('vapor', 400.0, 0.004, v=46.13, h=2738.8, s=9.0035),
        StateData('vapor', 500.0, 1.0, v=0.2206, h=2890.2, s=6.8223),
        StateData('super', 800.0, 0.01, v=36.92, h=3546.0, s=9.9699),
        StateData('super', 900.0, 0.70, v=0.5917, h=3759.4, s=8.2621),
        StateData('super', 1000.0, 30.0, v=0.01421, h=3821.6, s=6.6373),
        StateData('liquid', 500.0, 3.0, rho=832.04, h=975.68, s=2.58049)]

    refState = StateData('critical', 647.286, 22.089, rho=317.0, h=2098.8, s=4.4289)
    name = "water"
    tol = Tolerances(2e-3, 2e-3, 2e-3)


@pytest.fixture(scope='function')
def pure_fluid(request):
    request.cls.fluid = ct.Water()

@pytest.mark.usefixtures('pure_fluid')
class TestPureFluidConvergence:

    def test_TP(self):
        # Focus on the region near the critical point
        TT = [273.161, 300.0, 350.0, 400.0, 500.0,
              600.0, 640.0, 645.0, 646.0, 647.0,
              647.1, 647.2, 647.22, 647.23, 647.25,
              647.26, 647.27, 647.28, 647.282, 647.284,
              647.285, 647.286, 647.287, 650.0, 800.0]
        PP = [1234.0, 101325.0, 5e5, 22.0e6, 22.08e6, 22.09e6, 10001000.0]

        errors = ''
        nErrors = 0
        for T,P in itertools.product(TT, PP):
            try:
                self.fluid.TP = T, P
                assert self.fluid.T == approx(T, rel=1e-6)
                assert self.fluid.P == approx(P, rel=1e-6)
            except Exception as e:
                errors += 'Error at T=%r, P=%r:\n%s\n\n' % (T,P,e)
                nErrors += 1
        if errors:
            errors += 'Total error count:%s\n' % nErrors
            raise AssertionError(errors)

    def test_UV(self):
        u0 = -1.58581e7
        UU = np.array([0, 100, 200, 500, 1000, 1500, 2000]) * 1000 + u0
        VV = [0.001, 0.002, 0.005, 0.010, 0.10, 0.5, 1.0, 1.5, 2.0]
        errors = ''
        nErrors = 0
        for u,v in itertools.product(UU, VV):
            try:
                self.fluid.UV = u, v
                assert self.fluid.u == approx(u, rel=1e-6)
                assert self.fluid.v == approx(v, rel=1e-6)
            except Exception as e:
                errors += 'Error at u=%r, v=%r:\n%s\n\n' % (u,v,e)
                nErrors += 1
        if errors:
            errors += 'Total error count:%s\n' % nErrors
            raise AssertionError(errors)

    def test_HP(self):
        h0 = -1.58581e7
        HH = np.array([0, 100, 200, 500, 1000, 1500, 2000]) * 1000 + h0
        PP = [1234.0, 101325.0, 5e5, 22.0e6, 22.08e6, 22.09e6, 10001000.0]
        errors = ''
        nErrors = 0
        for h,P in itertools.product(HH, PP):
            try:
                self.fluid.HP = h, P
                assert self.fluid.h == approx(h, rel=1e-6)
                assert self.fluid.P == approx(P, rel=1e-6)
            except Exception as e:
                errors += 'Error at h=%r, P=%r:\n%s\n\n' % (h,P,e)
                nErrors += 1
        if errors:
            errors += 'Total error count:%s\n' % nErrors
            raise AssertionError(errors)
