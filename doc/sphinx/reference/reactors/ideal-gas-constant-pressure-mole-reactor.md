```{py:currentmodule} cantera
```

# Ideal Gas Constant Pressure Mole Reactor

An ideal gas constant pressure mole reactor, as implemented by the C++ class
{ct}`IdealGasConstPressureMoleReactor` and available in Python as the
{py:class}`IdealGasConstPressureMoleReactor` class. It is defined by the state
variables:

- $T$, the temperature (in K)
- $n_k$, the number of moles for each species (in kmol)

Equations 1 and 2 below are the governing equations for an ideal gas constant pressure
mole reactor.

## Species Equations

The moles of each species in the reactor changes as a result of flow through the
reactor's [inlets and outlets](sec-flow-device), and production of homogeneous gas phase
species and reactions on the reactor [surfaces](sec-reactor-surface). The rate at which
species $k$ is generated through homogeneous phase reactions is $V \dot{\omega}_k$, and
the total rate at which moles of species $k$ changes is:

$$
\frac{dn_k}{dt} = V \dot{\omega}_k + \sum_{in} \dot{n}_{k, in}
                  - \sum_{out} \dot{n}_{k, out} + \dot{n}_{k, wall}
$$ (ig-const-pressure-mole-reactor-species)

Where the subscripts *in* and *out* refer to the sum of the corresponding property over
all inlets and outlets respectively. A dot above a variable signifies a time derivative.

## Energy Equation

As for the [ideal gas mole reactor](ideal-gas-mole-reactor), we replace the total
enthalpy as a state variable with the temperature by writing the total enthalpy in terms
of the species moles and temperature:

$$  H = \sum_k \hat{h}_k(T) n_k  $$

and differentiating with respect to time:

$$  \frac{dH}{dt} = \frac{dT}{dt}\sum_k n_k \hat{c}_{p,k} + \sum \hat{h}_k \dot{n}_k  $$

Substituting this into the energy equation for the constant pressure mole reactor
{eq}`const-pressure-mole-reactor-energy` yields an equation for the temperature:

$$
\sum_k n_k \hat{c}_{p,k} \frac{dT}{dt} = \dot{Q} - \sum \hat{h}_k \dot{n}_k
$$  (ig-const-pressure-mole-reactor-energy)