#include "gtest/gtest.h"
#include "cantera/thermo/ThermoPhase.h"
#include "cantera/thermo/ThermoFactory.h"
#include "cantera/base/Solution.h"
#include "cantera/base/utilities.h"

using namespace std;

namespace Cantera
{

vector<AnyMap> getStates(const string& name) {
    static AnyMap cases = AnyMap::fromYamlFile("consistency-cases.yaml");
    return cases[name]["states"].asVector<AnyMap>();
}

AnyMap getSetup(const string& name) {
    static AnyMap cases = AnyMap::fromYamlFile("consistency-cases.yaml");
    return cases[name]["input"].as<AnyMap>();
}

class TestConsistency : public testing::TestWithParam<std::tuple<AnyMap, AnyMap>>
{
public:
    TestConsistency() {
        auto param = GetParam();
        AnyMap inp = get<0>(param);
        AnyMap state = get<1>(param);
        pair<string, string> key = {inp["file"].asString(), inp.getString("phase", "")};
        if (cache.count(key) == 0) {
            cache[key].reset(newPhase(key.first, key.second));
        }
        atol = inp.getDouble("atol", 1e-5);

        phase = cache[key];
        phase->setState(state);
        nsp = phase->nSpecies();
        p = phase->pressure();
        T = phase->temperature();
    }

    static map<pair<string, string>, shared_ptr<ThermoPhase>> cache;

    shared_ptr<ThermoPhase> phase;
    size_t nsp;
    double T, p;
    double atol;
};

map<pair<string, string>, shared_ptr<ThermoPhase>> TestConsistency::cache = {};

TEST_P(TestConsistency, h_eq_u_plus_Pv) {
    double h = phase->enthalpy_mole();
    double u = phase->intEnergy_mole();
    double v = phase->molarVolume();
    EXPECT_NEAR(h, u + p * v, atol);
}

TEST_P(TestConsistency, g_eq_h_minus_Ts) {
    double g = phase->gibbs_mole();
    double h = phase->enthalpy_mole();
    double s = phase->entropy_mole();
    EXPECT_NEAR(g, h - T * s, atol);
}

TEST_P(TestConsistency, hk_eq_uk_plus_P_times_vk)
{
    vector_fp hk(nsp), uk(nsp), vk(nsp);
    phase->getPartialMolarEnthalpies(hk.data());
    phase->getPartialMolarIntEnergies(uk.data());
    phase->getPartialMolarVolumes(vk.data());
    for (size_t k = 0; k < nsp; k++) {
        EXPECT_NEAR(hk[k], uk[k] + p * vk[k], atol);
    }
}

TEST_P(TestConsistency, gk_eq_hk_minus_T_times_sk)
{
    vector_fp gk(nsp), hk(nsp), sk(nsp);
    phase->getChemPotentials(gk.data());
    phase->getPartialMolarEnthalpies(hk.data());
    phase->getPartialMolarEntropies(sk.data());
    for (size_t k = 0; k < nsp; k++) {
        EXPECT_NEAR(gk[k], hk[k] - T * sk[k], atol);
    }
}

TEST_P(TestConsistency, h_eq_sum_hk_Xk)
{
    vector_fp hk(nsp);
    phase->getPartialMolarEnthalpies(hk.data());
    EXPECT_NEAR(phase->enthalpy_mole(), phase->mean_X(hk), atol);
}

TEST_P(TestConsistency, u_eq_sum_uk_Xk)
{
    vector_fp uk(nsp);
    phase->getPartialMolarIntEnergies(uk.data());
    EXPECT_NEAR(phase->intEnergy_mole(), phase->mean_X(uk), atol);
}

TEST_P(TestConsistency, g_eq_sum_gk_Xk)
{
    vector_fp gk(nsp);
    phase->getChemPotentials(gk.data());
    EXPECT_NEAR(phase->gibbs_mole(), phase->mean_X(gk), atol);
}

TEST_P(TestConsistency, s_eq_sum_sk_Xk)
{
    vector_fp sk(nsp);
    phase->getPartialMolarEntropies(sk.data());
    EXPECT_NEAR(phase->entropy_mole(), phase->mean_X(sk), atol);
}

TEST_P(TestConsistency, v_eq_sum_vk_Xk)
{
    vector_fp vk(nsp);
    phase->getPartialMolarVolumes(vk.data());
    EXPECT_NEAR(phase->molarVolume(), phase->mean_X(vk), atol);
}

INSTANTIATE_TEST_SUITE_P(IdealGas, TestConsistency,
    testing::Combine(
        testing::Values(getSetup("ideal-gas-h2o2")),
        testing::ValuesIn(getStates("ideal-gas-h2o2")))
);

INSTANTIATE_TEST_SUITE_P(RedlichKwong, TestConsistency,
    testing::Combine(
        testing::Values(getSetup("redlich-kwong")),
        testing::ValuesIn(getStates("redlich-kwong")))
);

}
