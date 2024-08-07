c     Isentropic flow
c     ===============
c
c     Calculated Mach number vs. area for an isentropic flow. Relies on
c     the wrapper functions defined in :doc:`demo_ftnlib.cpp
c     <demo_ftnlib>` to call the Cantera C++ interface.
c     See also the Python version of this problem in
c     :doc:`isentropic.py <../python/thermo/isentropic>`.
c
c     .. tags:: Fortran 77, compressible flow

c     This file is part of Cantera. See License.txt in the top-level directory or
c     at https://cantera.org/license.txt for license and copyright information.

      program isentropic
      implicit double precision (a-h,o-z)
      parameter (oneatm = 1.01325d5, NPTS = 200)
      double precision a(NPTS), dmach(NPTS), t(NPTS),
     $     ratio(NPTS)

      call newIdealGasMix('h2o2.yaml','ohmech','none')
      temp = 1200.d0
      pres = 10.d0*oneatm
      call setState_TPX_String(temp, pres,'H2:1, N2:0.1')

c     stagnation state properties
      s0 = entropy_mass()
      h0 = enthalpy_mass()
      p0 = pressure()

      dmdot = 1.0d0
      amin = 1.0d14

      do n = 1, NPTS
         p = p0*n/(NPTS+1)
         call setState_SP(s0,p)
         h = enthalpy_mass()
         rho = density()

         v2 = 2.0*(h0 - h)
         v = sqrt(v2)
         area = dmdot/(rho*v)
         if (area .lt. amin) then
            amin = area
         end if

         a(n) = area
         dmach(n) = v/soundspeed()
         t(n) = temperature()
         ratio(n) = p/p0
      end do

      do n = 1, NPTS
         a(n) = a(n)/amin
         write(*,30) a(n), dmach(n), t(n), ratio(n)
 30      format(4e16.5)
      end do
      end


      double precision function soundspeed()
      implicit double precision (a-h,o-z)
      double precision meanMolarMass
      parameter (R = 8314.4621d0)
      gamma = cp_mass()/cv_mass()
      soundspeed = sqrt(gamma * R * temperature()
     $     / meanMolarMass())
      return
      end
