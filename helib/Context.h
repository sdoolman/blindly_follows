/* Copyright (C) 2012-2020 IBM Corp.
 * This program is Licensed under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance
 * with the License. You may obtain a copy of the License at
 *   http://www.apache.org/licenses/LICENSE-2.0
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License. See accompanying LICENSE file.
 */
#ifndef HELIB_CONTEXT_H
#define HELIB_CONTEXT_H
/**
 * @file Context.h
 * @brief Keeps the parameters of an instance of the cryptosystem
 **/
#include <helib/PAlgebra.h>
#include <helib/CModulus.h>
#include <helib/IndexSet.h>
#include <helib/recryption.h>
#include <helib/primeChain.h>
#include <helib/powerful.h>
#include <helib/apiAttributes.h>
#include <helib/range.h>
#include <helib/scheme.h>

#include <NTL/Lazy.h>

#define FHE_DISABLE_CONTEXT_CONSTRUCTOR

namespace helib {

constexpr int MIN_SK_HWT = 120;
constexpr int BOOT_DFLT_SK_HWT = MIN_SK_HWT;

/**
 * @brief An estimate for the security-level. This has a lower bound of 0.
 * @param n LWE dimension.
 * @param log2AlphaInv Variable containing the value of `log(1/alpha)` where
 * `alpha` is the noise.
 * @param hwt The Hamming weight.
 * @return The estimated security level.
 * @note This function uses experimental affine approximations to the
 * lwe-estimator from
 * https://bitbucket.org/malb/lwe-estimator/raw/HEAD/estimator.py, from
 * Aug-2020 (see script in misc/estimator/lwe-estimator.sage). Let X = n /
 * log(1/alpha), the security level is estimated as follows:
 * ```
 *   + dense {-1,0,1} keys:      security ~ 3.8*X  -20
 *   + sparse keys (weight=450): security ~ 3.55*X -12
 *   + sparse keys (weight=420): security ~ 3.5*X  -10
 *   + sparse keys (weight=390): security ~ 3.45*X -7
 *   + sparse keys (weight=360): security ~ 3.4*X  -5
 *   + sparse keys (weight=330): security ~ 3.35*X -4
 *   + sparse keys (weight=300): security ~ 3.3*X  -3
 *   + sparse keys (weight=270): security ~ 3.2*X  +1
 *   + sparse keys (weight=240): security ~ 3.1*X  +3
 *   + sparse keys (weight=210): security ~ 3*X    +6
 *   + sparse keys (weight=180): security ~ 2.83*X +10
 *   + sparse keys (weight=150): security ~ 2.67*X +13
 *   + sparse keys (weight=120): security ~ 2.4*X  +19
 * ```
 */

inline double lweEstimateSecurity(int n, double log2AlphaInv, int hwt)
{
  if (hwt < 0 || (hwt > 0 && hwt < MIN_SK_HWT)) {
    return 0;
  }

  // clang-format off
  constexpr double hwgts[] =
      {120, 150, 180, 210, 240, 270, 300, 330, 360, 390, 420, 450};
  constexpr double slopes[] =
      {2.4, 2.67, 2.83, 3.0, 3.1, 3.3, 3.3, 3.35, 3.4, 3.45, 3.5, 3.55};
  constexpr double cnstrms[] =
      {19, 13, 10, 6, 3, 1, -3, -4, -5, -7, -10, -12};
  // clang-format on

  constexpr size_t numWghts = sizeof(hwgts) / sizeof(hwgts[0]);

  const size_t idx = (hwt - 120) / 30; // index into the array above
  double slope = 0, consterm = 0;
  if (hwt == 0) { // dense keys
    slope = 3.8;
    consterm = -20;
  } else if (idx < numWghts - 1) {
    // estimate prms on a line from prms[i] to prms[i+1]
    // how far into this interval
    double a = double(hwt - hwgts[idx]) / (hwgts[idx + 1] - hwgts[idx]);
    slope = slopes[idx] + a * (slopes[idx + 1] - slopes[idx]);
    consterm = cnstrms[idx] + a * (cnstrms[idx + 1] - cnstrms[idx]);
  } else {
    // Use the params corresponding to largest weight (450 above)
    slope = slopes[numWghts - 1];
    consterm = cnstrms[numWghts - 1];
  }

  double x = n / log2AlphaInv;
  double ret = slope * x + consterm;

  return ret < 0.0 ? 0.0 : ret; // If ret is negative then return 0.0
}

/**
 * @brief Returns smallest parameter m satisfying various constraints:
 * @param k security parameter
 * @param L number of levels
 * @param c number of columns in key switching matrices
 * @param p characteristic of plaintext space
 * @param d embedding degree (d ==0 or d==1 => no constraint)
 * @param s at least that many plaintext slots
 * @param chosen_m preselected value of m (0 => not preselected)
 * Fails with an error message if no suitable m is found
 * prints an informative message if verbose == true
 **/
long FindM(long k,
           long nBits,
           long c,
           long p,
           long d,
           long s,
           long chosen_m,
           bool verbose = false);

class EncryptedArray;
struct PolyModRing;

// Forward declaration of ContextBuilder
template <typename SCHEME>
class ContextBuilder;

/**
 * @class Context
 * @brief Maintaining the parameters
 **/
class Context
{
  std::vector<Cmodulus> moduli; // Cmodulus objects for the different primes
  // This is private since the implementation assumes that the list of
  // primes only grows and no prime is ever modified or removed.

public:
  // Here are some "getter" methods that give direct
  // access to important parameters.  These are for convenience,
  // as well as allowing for future re-organization.

  // Parameters stored in zMStar.
  // These are invariant for any computations involving this Context

  /**
   * @brief Getter method for the `m` used to create this `context`.
   * @return The cyclotomic index `m`.
   **/
  long getM() const { return zMStar.getM(); }

  /**
   * @brief Getter method for the `p` used to create this `context`.
   * @return The plaintext modulus `p`.
   **/
  long getP() const { return zMStar.getP(); }

  /**
   * @brief Getter method for the `phi(m)` of the created `context`.
   * @return The degree of the cyclotomic polynomial `Phi_m(X)`.
   **/
  long getPhiM() const { return zMStar.getPhiM(); }

  /**
   * @brief Getter method for the `ord(p)` of the created `context`.
   * @return The order of `p` in `(Z/mZ)^*`.
   **/
  long getOrdP() const { return zMStar.getOrdP(); }

  /**
   * @brief Getter method for the number of plaintext slots of the created
   * `context`.
   * @return The number of plaintext slots `phi(m)/ord(p)`.
   **/
  long getNSlots() const { return zMStar.getNSlots(); }

  // Parameters stored in alMod.
  // These are NOT invariant: it is possible to work
  // with View objects that use a different PAlgebra object.

  /**
   * @brief Getter method for the default `r` value of the created `context`.
   * @return The `r` value representing the Hensel lifting for `BGV` or the bit
   * precision for `CKKS`.
   * @note This value is not invariant: it is possible to work "view" objects
   * that use different `PAlgebra` objects.
   **/
  long getDefaultR() const { return alMod.getR(); }

  /**
   * @brief Getter method for the default `p^r` value of the created `context`.
   * @return The raised plaintext modulus `p^r`.
   * @note This value is not invariant: it is possible to work "view" objects
   * that use different `PAlgebra` objects.
   **/
  long getDefaultPPowR() const { return alMod.getPPowR(); }

  // synonymn for getDefaultR().
  // this is used in various corner cases in CKKS where
  // we really need some default precisiion parameter.
  // It is also possible to define this differently
  // in the future.
  /**
   * @brief Getter method for the default `precision` value of the created
   * `CKKS` `context`.
   * @return The bit `precision` value.
   * @note This value is not invariant: it is possible to work "view" objects
   * that use different `PAlgebra` objects.
   **/
  long getDefaultPrecision() const { return alMod.getR(); }

  bool isCKKS() const { return alMod.getTag() == PA_cx_tag; }

  //============================================================

  //! @brief The structure of Zm*.
  PAlgebra zMStar;

  //! @brief The structure of Z[X]/(Phi_m(X),p^r).
  PAlgebraMod alMod;

  //! @brief A default EncryptedArray.
  // VJS-FIXME: should this really be public?
  std::shared_ptr<const EncryptedArray> ea;

  /**
   * @brief Getter method returning the default `view` object of the created
   * `context`.
   * @return A reference to the `view` object.
   **/
  const EncryptedArray& getDefaultView() const { return *ea; } // preferred name
  // FIXME: This is deprecated and superseded by the above.
  const EncryptedArray& getDefaultEA() const { return *ea; } // legacy name

  std::shared_ptr<const PowerfulDCRT> pwfl_converter;

  /**
   * @brief The structure of a single slot of the plaintext space.
   * @note This will be Z[X]/(G(x),p^r) for some irreducible factor G of
   * Phi_m(X).
   **/
  std::shared_ptr<PolyModRing> slotRing;

  //! @brief The `sqrt(variance)` of the LWE error (default=3.2).
  NTL::xdouble stdev;

  //======================= high probability bounds ================
  double scale; // default = 10

  //! erfc(scale/sqrt(2)) * phi(m) should be less than some negligible
  //! parameter epsilon.
  //! The default value of 10 should be good enough for most applications.
  //! NOTE: -log(erfc(8/sqrt(2)))/log(2)  = 49.5
  //!       -log(erfc(10/sqrt(2)))/log(2) = 75.8
  //!       -log(erfc(11/sqrt(2)))/log(2) = 91.1
  //!       -log(erfc(12/sqrt(2)))/log(2) =107.8

  //! The way this is used is as follows. If we have a normal random
  //! variable X with variance sigma^2, then the probability that
  //! that X lies outside the interval [-scale*sigma, scale*sigma] is
  //! delta=erfc(scale/sqrt(2)). We will usually apply the union bound
  //! to a vector of phi(m) such random variables (one for each primitive
  //! m-th root of unity), so that the probability that that the L-infty
  //! norm exceeds scale*sigma is at most epsilon=phim*delta. Thus,
  //! scale*sigma will be used as a high-probability bound on the
  //! L-infty norm of such vectors.

  //=======================================

  //! Assume the polynomial f(x) = sum_{i < k} f_i x^i is chosen so
  //! that each f_i is chosen uniformly and independently from the
  //! interval [-magBound, magBound], and that k = degBound.
  //! This returns a bound B such that the L-infty norm
  //! of the canonical embedding exceeds B with probability at most
  //! epsilon.

  // NOTE: this is a bit heuristic: we assume that if we evaluate
  // f at a primitive root of unity, then we get something that well
  // approximates a normal random variable with the same variance,
  // which is equal to the sum of the variances of the individual
  // f_i's, which is (2*magBound)^2/12 = magBound^2/3.
  // We then multiply the sqrt of the variance by scale to get
  // the high probability bound.

  double noiseBoundForUniform(double magBound, long degBound) const
  {
    return scale * std::sqrt(double(degBound) / 3.0) * magBound;
  }

  NTL::xdouble noiseBoundForUniform(NTL::xdouble magBound, long degBound) const
  {
    return scale * std::sqrt(double(degBound) / 3.0) * magBound;
  }

  //=======================================

  //! Assume the polynomial f(x) = sum_{i < k} f_i x^i is chosen so
  //! that each f_i is chosen uniformly and independently from the
  //! from the set of balanced residues modulo the given modulus.
  //! This returns a bound B such that the L-infty norm
  //! of the canonical embedding exceeds B with probability at most
  //! epsilon.

  // NOTE: for odd modulus, this means each f_i is uniformly distributed
  // over { -floor(modulus/2), ..., floor(modulus/2) }.
  // For even modulus, this means each f_i is uniformly distributed
  // over { modulus/2, ..., modulus/2 }, except that the two endpoints
  // (which represent the same residue class) occur with half the
  // probability of the others.

  // NOTE: this is a bit heuristic: we assume that if we evaluate
  // f at a primitive root of unity, then we get something that well
  // approximates a normal random variable with the same variance,
  // which is equal to the sum of the variances of the individual
  // f_i's, which is (modulus)^2/12 + 1/6 for even modulus,
  // and is at most (modulus^2)/12 for odd modulus.
  // We then multiply the sqrt of the variance by scale to get
  // the high probability bound.

  // NOTE: this is slightly more accurate that just calling
  // noiseBoundForUniform with magBound=modulus/2.

  double noiseBoundForMod(long modulus, long degBound) const
  {
    double var = fsquare(modulus) / 12.0;
    if (modulus % 2 == 0)
      var += 1.0 / 6.0;

    return scale * std::sqrt(degBound * var);
  }

  //=======================================

  //! Assume the polynomial f(x) = sum_{i < k} f_i x^i is chosen
  //! so that each f_i is chosen uniformly and independently from
  //! N(0, sigma^2), and that k = degBound.
  //! This returns a bound B such that the L-infty norm
  //! of the canonical embedding exceeds B with probability at most
  //! epsilon.

  // NOTE: if we evaluate f at a primitive root of unity,
  // then we get a normal random variable variance degBound * sigma^2.
  // We then multiply the sqrt of the variance by scale to get
  // the high probability bound.

  double noiseBoundForGaussian(double sigma, long degBound) const
  {
    return scale * std::sqrt(double(degBound)) * sigma;
  }

  //=======================================

  //! Assume the polynomial f(x) = sum_{i < k} f_i x^i is chosen
  //! so that each f_i is zero with probability 1-prob, 1 with probability
  //! prob/2, and -1 with probability prob/2.
  //! This returns a bound B such that the L-infty norm
  //! of the canonical embedding exceeds B with probability at most
  //! epsilon.

  // NOTE: this is a bit heuristic: we assume that if we evaluate
  // f at a primitive root of unity, then we get something that
  // well approximates a normal random variable with the same variance,
  // which is equal to the sum of the individual variances,
  // which is degBound*prob.
  // We then multiply the sqrt of the variance by scale to get
  // the high probability bound.

  double noiseBoundForSmall(double prob, long degBound) const
  {
    return scale * std::sqrt(double(degBound)) * std::sqrt(prob);
  }

  //=======================================

  //! Assume the polynomial f(x) = sum_{i < k} f_i x^i is chosen
  //! hwt coefficients are chosen to \pm 1, and the remainder zero.
  //! This returns a bound B such that the L-infty norm
  //! of the canonical embedding exceeds B with probability at most
  //! epsilon.

  // NOTE: this is a bit heuristic: we assume that if we evaluate
  // f at a primitive root of unity, then we get something that
  // well approximates a normal random variable with the same variance,
  // which is hwt.
  // We then multiply the sqrt of the variance by scale to get
  // the high probability bound.

  // NOTE: degBound is not used here, but I include it
  // for consistency with the other noiseBound routines

  double noiseBoundForHWt(long hwt, UNUSED long degBound) const
  {
    return scale * std::sqrt(double(hwt));
  }

  //=======================================

  //! This computes a high probability bound on the L-infty norm
  //! of x0+s*x1 in the pwrfl basis, assuming is chosen with coeffs
  //! in the pwrfl basis uniformly and independently dist'd over [-1/2,1/2],
  //! x0 has arbitrary coeffs over [-1/2,1/2] in the pwrfl basis,
  //! and assuming s is chosen with skHwt nonzero coeffs mod X^m-1
  //! in the power basis (uniformly and independently over {-1,1}).
  //! The bound should be satisfied with probability epsilon.

  //! NOTE: this is a bit heuristic. See design document for details.

  //! NOTE: this is still valid even when m is a power of 2

  double stdDevForRecryption() const
  {
    long skHwt = hwt_param;

    long k = zMStar.getNFactors();
    // number of prime factors of m

    long m = zMStar.getM();
    long phim = zMStar.getPhiM();

    double mrat = double(phim) / double(m);

    return std::sqrt(mrat * double(skHwt) * double(1L << k) / 3.0) * 0.5;
  }

  double boundForRecryption() const
  {
    double c_m = zMStar.get_cM();
    // multiply by this fudge factor
    // VJS-FIXME: this fudge factor has to go

    return 0.5 + c_m * scale * stdDevForRecryption();
  }

  /**
   * The "ciphertext primes" are the "normal" primes that are used to
   * represent the public encryption key and ciphertexts. These are all
   * "large" single=precision primes, or bit-size roughly NTL_SP_SIZE bits.
   **/
  IndexSet ctxtPrimes;

  //! A disjoint set of primes, used for key switching. See section 3.1.6
  //! in the design document (key-switching). These too are "large"
  //! single=precision primes, or bit-size close to NTL_SP_SIZE bits.
  IndexSet specialPrimes;

  //! Yet a third set of primes, aimed at allowing modulus-switching with
  //! higher resolution. These are somewhat smaller single-precision
  //! primes, of size from NTL_SP_SIZE-20 to NTL_SP_SIZE-1.
  IndexSet smallPrimes;

  //! A helper table to map required modulo-sizes to primeSets
  ModuliSizes modSizes;
  void setModSizeTable() { modSizes.init(*this); }

  /**
   * @brief The set of primes for the digits.
   *
   * The different columns in any key-switching matrix contain encryptions
   * of multiplies of the secret key, sk, B1*sk, B2*B1*sk, B3*B2*B1*sk,...
   * with each Bi a product of a few "non-special" primes in the chain. The
   * digits data member indicate which primes correspond to each of the Bi's.
   * These are all IndexSet objects, whose union is the subset ctxtPrimes.
   *
   * The number of Bi's is one less than the number of columns in the key
   * switching matrices (since the 1st column encrypts sk, without any Bi's),
   * but we keep in the digits std::vector also an entry for the primes that do
   * not participate in any Bi (so digits.size() is the same as the number
   * of columns in the key switching matrices).
   * See section 3.1.6 in the design document (key-switching).
   **/
  // Digits of ctxt/columns of key-switching matrix
  std::vector<IndexSet> digits;

  //! Bootstrapping-related data in the context
  // includes both thin and thick
  ThinRecryptData rcData;

  //=======================================

  // These parameters are currently set by buildPrimeChain

  long hwt_param = 0; // Hamming weight of all keys associated with context
                      // 0 means "dense"

  long e_param = 0; // parameters specific to bootstrapping
  long ePrime_param = 0;

  /******************************************************************/
  // constructor
  /**
   * @brief Constructor for the `Context` object.
   * @param m The index of the cyclotomic polynomial.
   * @param p The plaintext modulus.
   * @param r BGV: The Hensel lifting parameter. CKKS: The bit precision.
   * @param gens The generators of `(Z/mZ)^*` (other than `p`).
   * @param ords The orders of each of the generators of `(Z/mZ)^*`.
   **/
  Context(unsigned long m,
          unsigned long p,
          unsigned long r,
          const std::vector<long>& gens = std::vector<long>(),
          const std::vector<long>& ords = std::vector<long>());

  // FIXME: This is a temporary fix to allow proper copy of the context.
  // Without the fixes there would be discrepancies between context's zMStar and
  // alMod const reference one.
  // TODO: Add doxygen comments to the following methods.
  /**
   * @brief Default destructor.
   **/
  ~Context() = default;

#ifdef FHE_DISABLE_CONTEXT_CONSTRUCTOR
  /**
   * @brief Default copy constructor.
   * @param other `Context` to copy.
   **/
  Context(const Context& other) = delete;

  /**
   * @brief Default move constructor.
   * @param other `Context` to copy.
   **/
  Context(Context&& other) = delete;

  template <typename SCHEME>
  explicit Context(const ContextBuilder<SCHEME>&);
  // Marked explicit to avoid dangerous implicit conversions.

#else

  /**
   * @brief Default copy constructor.
   * @param other `Context` to copy.
   **/
  Context(const Context& other);

  /**
   * @brief Default move constructor.
   * @param other `Context` to copy.
   **/
  Context(Context&& other);
#endif

  // Deleted assignment operators.
  Context& operator=(const Context& other) = delete;
  Context& operator=(Context&& other) = delete;

  /**
   * @brief Initialises the recryption data.
   * @param mvec A `std::vector` of unique prime factors of `m`.
   * @param build_cache Flag for building a cache for improved efficiency.
   * Default is false.
   * @param alsoThick Flag for initialising additional information needed for
   * thick bootstrapping. Default is true.
   **/
  void enableBootStrapping(const NTL::Vec<long>& mvec,
                           bool build_cache = false,
                           bool alsoThick = true)
  {
    assertTrue(e_param > 0,
               "enableBootStrapping invoked but willBeBootstrappable "
               "not set in buildModChain");

    rcData.init(*this, mvec, alsoThick, build_cache);
  }

  /**
   * @brief Check if a `Context` is bootstrappable.
   * @return `true` if recryption data is found, `false` otherwise.
   **/
  bool isBootstrappable() const { return rcData.alMod != nullptr; }

  /**
   * @brief Getter method that returns the handles of both the `ctxtPrimes` and
   * `specialPrimes` associated with this `Context`.
   * @return `IndexSet` of the handles to the `ctxtPrimes` and `specialPrimes`.
   **/
  IndexSet fullPrimes() const { return ctxtPrimes | specialPrimes; }

  /**
   * @brief Getter method that returns the handles of all primes associated with
   * this `Context`.
   * @return `IndexSet` of handles to the `ctxtPrimes`, `specialPrimes` and
   * `smallPrimes`.
   **/
  IndexSet allPrimes() const
  {
    return smallPrimes | ctxtPrimes | specialPrimes;
  }

  // returns first nprimes ctxtPrimes
  /**
   * @brief Getter method that returns the first `nprimes` `ctxtPrimes`
   * associated with this `Context`.
   * @param nprimes The number of desired `ctxtPrimes`.
   * @return `IndexSet` of handles to the first `nprimes` `ctxtPrimes`.
   **/
  IndexSet getCtxtPrimes(long nprimes) const
  {
    long first = ctxtPrimes.first();
    long last = std::min(ctxtPrimes.last(), first + nprimes - 1);
    return IndexSet(first, last);
  }

  // FIXME: replacement for bitsPerLevel...placeholder for now
  long BPL() const { return 30; }

  /**
   * @brief Equals operator between two `Context` objects.
   * @param other `Context` to compare to.
   * @return `true` if identical, `false` otherwise.
   **/
  bool operator==(const Context& other) const;

  /**
   * @brief Not equals operator between two `Context` objects.
   * @param other `Context` to compare to.
   * @return `true` if differ, `false` otherwise.
   **/
  bool operator!=(const Context& other) const { return !(*this == other); }

  /**
   * @brief Getter method for the small prime of the modulus chain at index
   * `i` as a `long`.
   * @param i Index of the desired small prime.
   * @return The small prime of the modulus chain at index `i`.
   **/
  long ithPrime(unsigned long i) const
  {
    return (i < moduli.size()) ? moduli[i].getQ() : 0;
  }

  /**
   * @brief Getter method for the small prime of the modulus chain at index
   * `i` as a `Cmodulus`.
   * @param i Index of the desired small prime.
   * @return Reference to the small prime modulus at index `i`.
   **/
  const Cmodulus& ithModulus(unsigned long i) const { return moduli[i]; }

  /**
   * @brief Return the total number of small primes in the modulus chain.
   * @return The total number of small primes in the modulus chain.
   **/
  long numPrimes() const { return moduli.size(); }

  /**
   * @brief Check if a number is divisible by any of the primes in the modulus
   * chain.
   * @param num The number to check.
   * @return `true` if the modulus chain contains at least one divisor of
   * `num`, false otherwise.
   **/
  bool isZeroDivisor(const NTL::ZZ& num) const
  {
    for (long i : range(moduli.size()))
      if (divide(num, moduli[i].getQ()))
        return true;
    return false;
  }

  /**
   * @brief Check if value is already contained within the modulus chain.
   * @param p The number to check.
   * @return `true` if `p` is already contained within the modulus chain,
   * `false` otherwise.
   **/
  bool inChain(long p) const
  {
    for (long i : range(moduli.size()))
      if (p == moduli[i].getQ())
        return true;
    return false;
  }

  ///@{
  /**
   * @brief Calculate the product of all primes in the given set.
   * @param p The product of the input primes.
   * @param s The set of input primes to the product.
   **/
  void productOfPrimes(NTL::ZZ& p, const IndexSet& s) const;
  NTL::ZZ productOfPrimes(const IndexSet& s) const
  {
    NTL::ZZ p;
    productOfPrimes(p, s);
    return p;
  }
  ///@}

  // FIXME: run-time error when ithPrime(i) returns 0
  /**
   * @brief Calculate the natural logarithm of the `i`th prime of the modulus
   * chain.
   * @param i Index of the desired prime.
   * @return The natural logarithm of the `i`th prime of the modulus chain.
   **/
  double logOfPrime(unsigned long i) const { return log(ithPrime(i)); }

  /**
   * @brief Calculate the natural logarithm of `productOfPrimes(s)` for a given
   * set of primes `s`.
   * @param s The set of input primes.
   * @return The natural logarithm of the product of the input primes.
   **/
  double logOfProduct(const IndexSet& s) const
  {
    if (s.last() >= numPrimes())
      throw RuntimeError("Context::logOfProduct: IndexSet has too many rows");

    double ans = 0.0;
    for (long i : s)
      ans += logOfPrime(i);
    return ans;
  }

  /**
   * @brief Calculate the size of the ciphertext modulus `Q` in bits.
   * @return The bit size of the ciphertext modulus `Q = ctxtPrimes |
   * specialPrimes`.
   **/
  long bitSizeOfQ() const
  {
    IndexSet primes = ctxtPrimes | specialPrimes;
    return std::ceil(logOfProduct(primes) / log(2.0));
  }

  /**
   * @brief An estimate for the security-level. This has a lower bound of 0.
   * @param hwt The Hamming weight of the secret key.
   *
   * @note This function uses experimental affine approximations to the
   * lwe-estimator from
   * https://bitbucket.org/malb/lwe-estimator/raw/HEAD/estimator.py, from
   * Aug-2020 (see script in misc/estimator/lwe-estimator.sage).
   *
   * Let s=3.2 if m is a power of two, or s=3.2*sqrt(m) otherwise. For the
   * estimator we use alpha=s/q (so log2AlphaInv = log_2(q/s)), and n=phi(m).
   */
  double securityLevel() const
  {
    IndexSet primes = ctxtPrimes | specialPrimes;
    if (primes.card() == 0) {
      throw LogicError(
          "Security level cannot be determined as modulus chain is empty.");
    }

    double s = to_double(stdev);
    if (zMStar.getPow2() == 0) { // not power of two
      s *= sqrt(zMStar.getM());
    }
    double log2AlphaInv = (logOfProduct(primes) - log(s)) / log(2.0);
    return lweEstimateSecurity(zMStar.getPhiM(), log2AlphaInv, hwt_param);
  }

  /**
   * @brief Print out algebra and other important info
   * @param out Output `std::ostream`.
   **/
  void printout(std::ostream& out = std::cout) const;

  /**
   * @brief Add the given prime to the `smallPrimes` set.
   * @param q The prime to add.
   **/
  void AddSmallPrime(long q);

  /**
   * @brief Add the given prime to the `ctxtPrimes` set.
   * @param q The prime to add.
   **/
  void AddCtxtPrime(long q);

  /**
   * @brief Add the given prime to the `specialPrimes` set.
   * @param q The prime to add.
   **/
  void AddSpecialPrime(long q);

  ///@{
  /**
     @name I/O routines

  To write out all the data associated with a context, do the following:

  \code
    writeContextBase(str, context);
    str << context;
  \endcode

  The first function call writes out just [m p r gens ords], which is the
  data needed to invoke the context constructor.

  The second call writes out all other information, including the
  stdev field, the prime sequence (including which primes are "special"),
  and the digits info.

  To read in all the data associated with a context, do the following:

  \code
    unsigned long m, p, r;
    std::vector<long> gens, ords;

    readContextBase(str, m, p, r, gens, ords);

    Context context(m, p, r, gens, ords);

    str >> context;
  \endcode

  The call to readContextBase just reads the values m, p, r and the set
  of generators in Zm* /(p) and their order. Then, after constructing the
  context, the >> operator reads in and attaches all other information.
  **/

  /**
   * @brief Write out the basic information `m`, `p` and `r` of the given
   * `Context` object.
   * @param str Output `std::ostream`.
   * @param context The `Context` to write.
   **/
  friend void writeContextBase(std::ostream& str, const Context& context);

  /**
   * @brief Write out all other data associated with a given `Context` object.
   * @param str Output `std::ostream`.
   * @param context The `Context` to write.
   * @return Input `std::ostream` post writing.
   **/
  friend std::ostream& operator<<(std::ostream& str, const Context& context);

  /**
   * @brief Read in the basic information `m`, `p` and `r` required to
   * construct a `Context` object.
   * @param str Input `std::istream`.
   * @param m Destination of the index of the cyclotomic polynomial.
   * @param p Destination of the plaintext modulus.
   * @param r Destination of `BGV`: The Hensel lifting parameter. `CKKS`: The
   * bit precision.
   * @param gens Destination of the generators of `(Z/mZ)^*` (other than `p`).
   * @param ords Destination of the orders of each of the generators of
   * `(Z/mZ)^*`.
   **/
  friend void readContextBase(std::istream& str,
                              unsigned long& m,
                              unsigned long& p,
                              unsigned long& r,
                              std::vector<long>& gens,
                              std::vector<long>& ords);

  /**
   * @brief Read in all other data associated with a given `Context` object.
   * @param str Input `std::istream`.
   * @param context Destination `Context` object.
   * @return Input `std::istream` post reading.
   **/
  friend std::istream& operator>>(std::istream& str, Context& context);
  ///@}

  friend void writeContextBinary(std::ostream& str, const Context& context);
  friend void readContextBinary(std::istream& str, Context& context);

  // internal function to undo buldModChain...used for parameter
  // generation programs

  void clearModChain()
  {
    moduli.clear();
    ctxtPrimes.clear();
    specialPrimes.clear();
    smallPrimes.clear();
    modSizes.clear();
    digits.clear();
    hwt_param = 0;
    e_param = 0;
    ePrime_param = 0;
  }
};

//! @brief write [m p r gens ords] data
void writeContextBase(std::ostream& s, const Context& context);
//! @brief read [m p r gens ords] data, needed to construct context
void readContextBase(std::istream& s,
                     unsigned long& m,
                     unsigned long& p,
                     unsigned long& r,
                     std::vector<long>& gens,
                     std::vector<long>& ords);
std::unique_ptr<Context> buildContextFromAscii(std::istream& str);

//! @brief write [m p r gens ords] data
void writeContextBaseBinary(std::ostream& str, const Context& context);
void writeContextBinary(std::ostream& str, const Context& context);

//! @brief read [m p r gens ords] data, needed to construct context
void readContextBaseBinary(std::istream& s,
                           unsigned long& m,
                           unsigned long& p,
                           unsigned long& r,
                           std::vector<long>& gens,
                           std::vector<long>& ords);

std::unique_ptr<Context> buildContextFromBinary(std::istream& str);
void readContextBinary(std::istream& str, Context& context);

// Build modulus chain with nBits worth of ctxt primes,
// using nDgts digits in key-switching.

/**
 * @brief Build the modulus chain for given `Context` object.
 * @param nBits Total number of bits required for the modulus chain.
 * @param nDgts Number of digits/columns in the key-switching matrix. Default
 * is 3.
 * @param willBeBoostrappable Flag for initializing bootstrapping data. Default
 * is `false`.
 * @param skHwt The Hamming weight of the secret key. Default is 0.
 * @param resolution The bit size of resolution of the modulus chain. Default
 * is 3.
 * @param bitsInSpecialPrimes The bit size of the special primes in the modulus
 * chain. Default is 0.
 **/
void buildModChain(Context& context,
                   long nBits,
                   long nDgts = 3,
                   bool willBeBootstrappable = false,
                   long skHwt = 0,
                   long resolution = 3,
                   long bitsInSpecialPrimes = 0);

// should be called if after you build the mod chain in some way
// *other* than calling buildModChain.
void endBuildModChain(Context& context);

/**
 * @brief `ostream` operator for serializing the `ContextBuilder` object.
 * @tparam SCHEME The encryption scheme to be used, must be `BGV` or `CKKS`.
 * @param os Reference to the output stream.
 * @param cb The `ContextBuilder` object to serialize.
 * @return Reference to the `std::ostream`
 **/
template <typename SCHEME>
std::ostream& operator<<(std::ostream& os, const ContextBuilder<SCHEME>& cb);

/**
 * @class ContextBuilder
 * @brief Builder to help construct a context.
 * @tparam SCHEME The encryption scheme to be used, must be `BGV` or `CKKS`.
 **/
template <typename SCHEME>
class ContextBuilder
{
  static_assert(std::is_same<SCHEME, CKKS>::value ||
                    std::is_same<SCHEME, BGV>::value,
                "Can only create context object parameterized by the crypto "
                "scheme (CKKS or BGV)");

private:
  // Default values by scheme.
  struct default_values;

  // General parameters
  std::vector<long> gens_;
  std::vector<long> ords_;
  long m_ = default_values::m; // BGV: 3, CKKS: 4
  long p_ = default_values::p; // BGV: 2, CKKS: -1
  long r_ = default_values::r; // BGV: Hensel lifting = 1,
                               // CKKS: Precision = 20
  long c_ = 3;

  // Modulus chain params
  long bits_ = 300;
  long skHwt_ = 0;
  long resolution_ = 3;
  long bitsInSpecialPrimes_ = 0;
  bool buildModChainFlag_ = true; // Default build the modchain.

  // Boostrap params (BGV only)
  NTL::Vec<long> mvec_;
  bool buildCacheFlag_ = false;
  bool thickFlag_ = false;
  bool bootstrappableFlag_ = false; // Default not boostrappable.

public:
  /**
   * @brief Sets `m` the order of the cyclotomic polynomial.
   * @param m The order of the cyclotomic polynomial.
   * @return Reference to this `ContextBuilder` object.
   **/
  ContextBuilder& m(long m)
  {
    m_ = m;
    return *this;
  }

  /**
   * @brief Sets `p` the prime number of the ciphertext space.
   * @param p The prime number of the plaintext space.
   * @return Reference to the `ContextBuilder` object.
   * @note Only exists when the `SCHEME` is `BGV`.
   **/
  template <typename S = SCHEME,
            std::enable_if_t<std::is_same<S, BGV>::value>* = nullptr>
  ContextBuilder& p(long p)
  {
    p_ = p;
    return *this;
  }

  /**
   * @brief Sets `r` the Hensel lifting parameter.
   * @param r The Hensel lifting parameter.
   * @return Reference to the `ContextBuilder` object.
   * @note Only exists when the `SCHEME` is `BGV`.
   **/
  template <typename S = SCHEME,
            std::enable_if_t<std::is_same<S, BGV>::value>* = nullptr>
  ContextBuilder& r(long r)
  {
    r_ = r;
    return *this;
  }

  /**
   * @brief Sets `precision` the bit precision parameter.
   * @param precision The bit precision parameter.
   * @return Reference to the `ContextBuilder` object.
   * @note Only exists when the `SCHEME` is `CKKS`.
   **/
  template <typename S = SCHEME,
            std::enable_if_t<std::is_same<S, CKKS>::value>* = nullptr>
  ContextBuilder& precision(long precision)
  {
    r_ = precision;
    return *this;
  }

  /**
   * @brief Sets `c` the number of columns (a.k.a. digits) in the key switching
   * matrices.
   * @param c The number of columns in the key switching matrix.
   * @return Reference to the `ContextBuilder` object.
   **/
  ContextBuilder& c(long c)
  {
    c_ = c;
    return *this;
  }

  /**
   * @brief Sets `gens` the generators of the `ZMStar` group.
   * @param gens A `std::vector` containing the generators.
   * @return Reference to the `ContextBuilder` object.
   **/
  ContextBuilder& gens(const std::vector<long>& gens)
  {
    gens_ = gens;
    return *this;
  }

  /**
   * @brief Sets `ords` the order of the corresponding generators in `gens` in
   * `ZmStar`.
   * @param ords A `std::vector` containing the orders of `gens`. The order
   * taken is the absolute value; a negative in `ords` represents a bad
   * dimension.
   * @return Reference to the `ContextBuilder` object.
   **/
  ContextBuilder& ords(const std::vector<long>& ords)
  {
    ords_ = ords;
    return *this;
  }

  /**
   * @brief Sets the bit size of the primes in the modulus chain.
   * @param bits How many bits to make the modulus chain.
   * @return Reference to the `ContextBuilder` object.
   * @note The actual bit size that is set is typically higher than requested.
   **/
  ContextBuilder& bits(long bits)
  {
    bits_ = bits;
    return *this;
  }

  /**
   * @brief Sets the secret key Hamming weight.
   * @param bits The secret key Hamming weight.
   * @return Reference to the `ContextBuilder` object.
   * @note If the Hamming weight is `0` (default) then a "dense" key will be
   * generated.
   **/
  ContextBuilder& skHwt(long skHwt)
  {
    skHwt_ = skHwt;
    return *this;
  }

  /**
   * @brief Sets the resolution for the modulus chain.
   * @param bits How many bit size of resolution.
   * @return Reference to the `ContextBuilder` object.
   **/
  ContextBuilder& resolution(long bits)
  {
    resolution_ = bits;
    return *this;
  }

  /**
   * @brief Sets the bit size of the special primes in the modulus chain.
   * @param bits The bit size of the special primes in the modulus chain.
   * @return Reference to this `ContextBuilder` object.
   **/
  ContextBuilder& bitsInSpecialPrimes(long bits)
  {
    bitsInSpecialPrimes_ = bits;
    return *this;
  }

  /**
   * @brief Sets a flag determining whether the modulus chain will be built.
   * @param `yesno` A `bool` to determine whether the modulus chain should be
   * built.
   * @return Reference to the `ContextBuilder` object.
   * @note `ContextBuilder` by default will build the modulus chain.
   **/
  ContextBuilder& buildModChain(bool yesno)
  {
    buildModChainFlag_ = yesno;
    return *this;
  }

  /**
   * @brief Sets `mvec` the unique primes which are factors of `m`.
   * @param mvec An `NTL::Vec` of primes factors.
   * @return Reference to the `ContextBuilder` object.
   * @note Only exists when the `SCHEME` is `BGV`.
   **/
  template <typename S = SCHEME,
            std::enable_if_t<std::is_same<S, BGV>::value>* = nullptr>
  ContextBuilder& mvec(const NTL::Vec<long>& mvec)
  {
    mvec_ = mvec;
    return *this;
  }

  /**
   * @brief Sets boostrapping to be `thin`.
   * @return Reference to the `ContextBuilder` object.
   * @note Only exists when the `SCHEME` is `BGV`.
   **/
  template <typename S = SCHEME,
            std::enable_if_t<std::is_same<S, BGV>::value>* = nullptr>
  ContextBuilder& thinboot()
  {
    thickFlag_ = false;
    return *this;
  }

  /**
   * @brief Sets boostrapping to be `thick`.
   * @return Reference to the `ContextBuilder` object.
   * @note Only exists when the `SCHEME` is `BGV`.
   **/
  template <typename S = SCHEME,
            std::enable_if_t<std::is_same<S, BGV>::value>* = nullptr>
  ContextBuilder& thickboot()
  {
    thickFlag_ = true;
    return *this;
  }

  /**
   * @brief Sets flag to choose that the cache for boostrapping will be
   * built.
   * @param yesno A `bool` to determine whether the cache is built.
   * @return Reference to the `ContextBuilder` object.
   * @note @note Only exists when the `SCHEME` is `BGV`.
   **/
  template <typename S = SCHEME,
            std::enable_if_t<std::is_same<S, BGV>::value>* = nullptr>
  ContextBuilder& buildCache(bool yesno)
  {
    buildCacheFlag_ = yesno;
    return *this;
  }

  /**
   * @brief Sets a flag determining if the context will be bootstrappable.
   * @param yesno A `bool` to determine whether the context will be
   * bootstrappable.
   * @return Reference to this `ContextBuilder` object.
   * @note `ContextBuilder` by default will not be bootstrappable.
   * @note Only exists when the `SCHEME` is `BGV`.
   **/
  template <typename S = SCHEME,
            std::enable_if_t<std::is_same<S, BGV>::value>* = nullptr>
  ContextBuilder& bootstrappable(bool yesno)
  {
    bootstrappableFlag_ = yesno;
    return *this;
  }

  /**
   * @brief Builds a `Context` object from the arguments stored in the
   * `ContextBuilder` object.
   * @return A `Context` object.
   **/
#ifdef FHE_DISABLE_CONTEXT_CONSTRUCTOR

  // compatibility interface
  ContextBuilder& build() { return *this; }

  friend class Context;
#else
  Context build() const;
#endif

  friend std::ostream& operator<<<SCHEME>(std::ostream& os,
                                          const ContextBuilder& cb);
};

// Default BGV values
template <>
struct ContextBuilder<BGV>::default_values
{
  static constexpr long m = 3;
  static constexpr long p = 2;
  static constexpr long r = 1;
};

// Default CKKS values
template <>
struct ContextBuilder<CKKS>::default_values
{
  static constexpr long m = 4;
  static constexpr long p = -1;
  static constexpr long r = 20;
};

///@}
// Should point to the "current" context
extern Context* activeContext;

} // namespace helib

#endif // ifndef HELIB_CONTEXT_H
