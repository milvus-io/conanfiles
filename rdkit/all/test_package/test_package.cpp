// Minimal smoke-test for the RDKit Conan package.

#include <GraphMol/GraphMol.h>
#include <GraphMol/SmilesParse/SmilesParse.h>
#include <GraphMol/SmilesParse/SmilesWrite.h>
#include <GraphMol/Fingerprints/MorganFingerprints.h>
#include <GraphMol/Substruct/SubstructMatch.h>
#include <DataStructs/ExplicitBitVect.h>

#include <iostream>
#include <memory>
#include <vector>

int main() {
    // 1. SMILES parse + write
    std::unique_ptr<RDKit::ROMol> mol(RDKit::SmilesToMol("c1ccccc1"));
    if (!mol) {
        std::cerr << "FAIL: could not parse SMILES\n";
        return 1;
    }
    std::cout << "SMILES   : OK (" << RDKit::MolToSmiles(*mol) << ")\n";

    // 2. Morgan fingerprint
    std::unique_ptr<ExplicitBitVect> mfp(
        RDKit::MorganFingerprints::getFingerprintAsBitVect(*mol, 2, 2048));
    if (!mfp || mfp->getNumBits() != 2048) {
        std::cerr << "FAIL: Morgan fingerprint\n";
        return 1;
    }
    std::cout << "Morgan FP: OK (" << mfp->getNumOnBits() << " on-bits)\n";

    // 3. Substructure match
    std::unique_ptr<RDKit::ROMol> query(RDKit::SmartsToMol("c1ccccc1"));
    RDKit::MatchVectType match;
    if (!RDKit::SubstructMatch(*mol, *query, match)) {
        std::cerr << "FAIL: substructure match\n";
        return 1;
    }
    std::cout << "Substruct: OK (" << match.size() << " atoms)\n";

    std::cout << "\nAll tests PASSED.\n";
    return 0;
}
