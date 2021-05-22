/* Depends on https://github.com/IBM-HElib/HElib */

#include <iostream>
#include <string>
#include <helib/helib.h>
#include <helib/binaryCompare.h>
#include <helib/binaryArith.h>
#include <helib/intraSlot.h>

int main(int argc, char *argv[])
{
  // Plaintext prime modulus.
  long p = 2;
  // Cyclotomic polynomial - defines phi(m).
  long m = 4095;
  // Hensel lifting (default = 1).
  long r = 1;
  // Number of bits of the modulus chain.
  long bits = 500;
  // Number of columns of Key-Switching matrix (typically 2 or 3).
  long c = 2;
  // Factorisation of m required for bootstrapping.
  std::vector<long> mvec = {7, 5, 9, 13};
  // Generating set of Zm* group.
  std::vector<long> gens = {2341, 3277, 911};
  // Orders of the previous generators.
  std::vector<long> ords = {6, 4, 6};

  std::cout << "Initialising context object..." << std::endl;
  // Initialize the context.
  // This object will hold information about the algebra created from the
  // previously set parameters.
  helib::Context context = helib::ContextBuilder<helib::BGV>()
                               .m(m)
                               .p(p)
                               .r(r)
                               .gens(gens)
                               .ords(ords)
                               .bits(bits)
                               .c(c)
                               .bootstrappable(true)
                               .mvec(mvec)
                               .build();

  // Print the context.
  context.printout();
  std::cout << std::endl;

  // Print the security level.
  std::cout << "Security: " << context.securityLevel() << std::endl;

  // Secret key management.
  std::cout << "Creating secret key..." << std::endl;
  // Create a secret key associated with the context.
  helib::SecKey secret_key(context);
  // Generate the secret key.
  secret_key.GenSecKey();

  // Generate bootstrapping data.
  secret_key.genRecryptData();

  // Public key management.
  // Set the secret key (upcast: SecKey is a subclass of PubKey).
  const helib::PubKey &public_key = secret_key;

  // Get the EncryptedArray of the context.
  const helib::EncryptedArray &ea = context.getEA();

  // Build the unpack slot encoding.
  std::vector<helib::zzX> unpackSlotEncoding;
  buildUnpackSlotEncoding(unpackSlotEncoding, ea);

  // Get the number of slot (phi(m)).
  long nslots = ea.size();
  std::cout << "Number of slots: " << nslots << std::endl;

  // Generate two random binary numbers a, mod.
  // Encrypt them under BGV.
  // Calculate a % mod with HElib's binary arithmetic functions, then decrypt
  // the result.

  // Each bit of the binary number is encoded into a single ciphertext. Thus
  // for a 16 bit binary number, we will represent this as an array of 16
  // unique ciphertexts.
  // i.e. b0 = [0] [0] [0] ... [0] [0] [0]        ciphertext for bit 0
  //      b1 = [1] [1] [1] ... [1] [1] [1]        ciphertext for bit 1
  //      b2 = [1] [1] [1] ... [1] [1] [1]        ciphertext for bit 2
  // These 3 ciphertexts represent the 3-bit binary number 110b = 6

  // Note: several numbers can be encoded across the slots of each ciphertext
  // which would result in several parallel slot-wise operations.
  // For simplicity we place the same data into each slot of each ciphertext,
  // printing out only the back of each vector.
  long bitSize = 4;
  long mod_data = NTL::RandomBits_long(bitSize);
  helib::assertInRange(mod_data, 1L, 8L, std::to_string(mod_data) + "is out of range");
  long a_data = NTL::RandomBnd(pow((mod_data - 1), 2) + 1);

  std::cout << "Pre-encryption data:" << std::endl;
  std::cout << "a = " << a_data << std::endl;
  std::cout << "m = " << mod_data << std::endl;

  // Use a scratch ciphertext to populate vectors.
  helib::Ctxt scratch(public_key);

  // Encrypt the data in 2's complement binary representation.
  std::vector<helib::Ctxt> encrypted_a(bitSize + 1, scratch);
  std::vector<helib::Ctxt> encrypted_mod(bitSize + 1, scratch);

  for (long i = 0; i < bitSize; ++i)
  {
    std::vector<long> a_vec(ea.size());
    std::vector<long> m_vec(ea.size());
    // Extract the i'th bit
    for (auto &slot : a_vec)
    {
      slot = (a_data >> i) & 1;
    }
    for (auto &slot : m_vec)
    {
      slot = (mod_data >> i) & 1;
    }
    ea.encrypt(encrypted_a[i], public_key, a_vec);
    ea.encrypt(encrypted_mod[i], public_key, m_vec);
  }
  std::vector<long> zero_vec(ea.size(), 0);
  ea.encrypt(encrypted_a[bitSize], public_key, zero_vec);
  ea.encrypt(encrypted_mod[bitSize], public_key, zero_vec);

  helib::Ctxt mu(scratch), ni(scratch);
  helib::CtPtrs_vectorCt a_wrapper(encrypted_a), mod_wrapper(encrypted_mod);

  std::vector<helib::Ctxt> encrypted_difference(bitSize + 1, scratch);
  helib::CtPtrs_vectorCt difference_wrapper(encrypted_difference);

  for (auto i = 0; i < mod_data; i++)
  {
    std::cout << "level=" << i + 1 << std::endl;
    helib::subtractBinary(difference_wrapper, a_wrapper, mod_wrapper, &unpackSlotEncoding);

    helib::compareTwoNumbers(mu, ni, a_wrapper, mod_wrapper, true, &unpackSlotEncoding); // mu = a < b
    helib::binaryCond(a_wrapper, ni, a_wrapper, difference_wrapper);

    mu.clear();
    ni.clear();
  }

  // Decrypt and print the result.
  std::vector<long> decrypted_result;
  helib::decryptBinaryNums(decrypted_result, a_wrapper, secret_key, ea, true);
  std::cout << "a % m = " << decrypted_result.back() << std::endl;

  return 0;
}