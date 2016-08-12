#include "G4MCPLGenerator.hh"
#include "G4ParticleGun.hh"
#include "G4RunManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4ParticleTable.hh"
#include "G4IonTable.hh"
#include "G4ios.hh"
#include <cassert>

///////////////////////////////////////////////////////////////////////////////////
//                                                                               //
// Implementation of G4MCPLGenerator class.                                      //
//                                                                               //
// This file can be freely used as per the terms in the LICENSE file.            //
//                                                                               //
// Written by Thomas Kittelmann, 2016.                                           //
//                                                                               //
///////////////////////////////////////////////////////////////////////////////////

G4MCPLGenerator::G4MCPLGenerator(const G4String& inputFile)
  : G4VUserPrimaryGeneratorAction(),
    m_currentPDG(0),
    m_currentPartDef(0),
    m_nUnknownPDG(0),
    m_inputFile(inputFile)
{
  m_mcplfile.internal = 0;
}

G4MCPLGenerator::~G4MCPLGenerator()
{
  if (m_nUnknownPDG) {
    std::ostringstream cmt;
    cmt << "Ignored a total of " << m_nUnknownPDG
        << " particles in input due to untranslatable pdg codes";
    G4Exception("G4MCPLGenerator::~G4MCPLGenerator()", "G4MCPLGenerator07",
                JustWarning, cmt.str().c_str());
  }
  if (m_mcplfile.internal)
    mcpl_close_file(m_mcplfile);
  delete m_gun;
}

bool G4MCPLGenerator::UseParticle(const mcpl_particle_t*) const
{
  return true;
}

void G4MCPLGenerator::ModifyParticle(G4ThreeVector&, G4ThreeVector&,
                                     G4ThreeVector&, G4double&, G4double&) const
{
}

void G4MCPLGenerator::GeneratePrimaries(G4Event* evt)
{
  if (!m_mcplfile.internal) {
    //Initialise:
    m_mcplfile = mcpl_open_file(m_inputFile.c_str());
    m_gun = new G4ParticleGun(1);
    FindNext();
    if (!m_p) {
      G4Exception("G4MCPLGenerator::G4MCPLGenerator()", "G4MCPLGenerator01",
                  RunMustBeAborted, "Not a single suitable particle found in input file");
    }
  }

  if (!m_p) {
    G4Exception("G4MCPLGenerator::GeneratePrimaries()", "G4MCPLGenerator02",
                RunMustBeAborted, "GeneratePrimaries called despite no suitable"
                " particles existing.");
    G4RunManager::GetRunManager()->AbortRun(false);//hard abort
    return;
  }

  //Transfer m_p info to gun and shoot:

  assert(m_currentPDG == m_p->pdgcode && m_currentPartDef);
  m_gun->SetParticleDefinition(m_currentPartDef);

  G4ThreeVector pos(m_p->position[0],m_p->position[1],m_p->position[2]);
  pos *= CLHEP::cm;
  G4ThreeVector dir(m_p->direction[0],m_p->direction[1],m_p->direction[2]);
  G4ThreeVector pol(m_p->polarisation[0],m_p->polarisation[1],m_p->polarisation[2]);
  double time = m_p->time*CLHEP::millisecond;
  double weight = m_p->weight;
  ModifyParticle(pos,dir,pol,time,weight);
  m_gun->SetParticleMomentumDirection( dir );
  m_gun->SetParticlePosition( pos);
  m_gun->SetParticleEnergy(m_p->ekin);//already in MeV and CLHEP::MeV=1
  m_gun->SetParticleTime(time);
  m_gun->SetParticlePolarization(pol);
  const G4int ivertex = evt->GetNumberOfPrimaryVertex();
  m_gun->GeneratePrimaryVertex(evt);
  if (weight!=1.0)
    evt->GetPrimaryVertex(ivertex)->SetWeight(weight);

  //Prepare for next.
  FindNext();
  if (!m_p) {
    G4cout << "G4MCPLGenerator: No more particles to use from input file after this event. Requesting soft abort of run." << G4endl;
    G4RunManager::GetRunManager()->AbortRun(true);//soft abort
  }
}

void G4MCPLGenerator::FindNext()
{
  while( ( m_p = mcpl_read(m_mcplfile) ) ) {

    if (!UseParticle(m_p))
      continue;

    if (!(m_p->weight>0.0)) {
      G4Exception("G4MCPLGenerator::GeneratePrimaries()", "G4MCPLGenerator03",
                  JustWarning, "Ignoring particle in input with invalid weight.");
      continue;
    }

    if (m_p->pdgcode==0) {
      G4Exception("G4MCPLGenerator::GeneratePrimaries()", "G4MCPLGenerator04",
                  JustWarning, "Ignoring particle in input with invalid pdg code (0).");
      continue;
    }

    if (!LookupPDG(m_p->pdgcode)) {
      ++m_nUnknownPDG;
      if (m_nUnknownPDG<=100) {
        std::ostringstream cmt;
        cmt << "Ignoring particle in input with untranslatable pdg code ("
            << m_p->pdgcode <<")";
        G4Exception("G4MCPLGenerator::GeneratePrimaries()", "G4MCPLGenerator05",
                    JustWarning, cmt.str().c_str());
        if (m_nUnknownPDG==100)
          G4Exception("G4MCPLGenerator::GeneratePrimaries()", "G4MCPLGenerator06",
                      JustWarning, "Limit reached. Suppressing further warnings"
                      " regarding untranslatable pdg codes");
      }
      continue;
    }
    break;
  }
}

G4ParticleDefinition* G4MCPLGenerator::LookupPDG(G4int pdgcode)
{
  if (m_currentPDG == pdgcode)
    return m_currentPartDef;
  m_currentPDG = pdgcode;
  std::map<G4int,G4ParticleDefinition*>::const_iterator it = m_pdg2pdef.find(pdgcode);
  if (it!=m_pdg2pdef.end()) {
    m_currentPartDef = it->second;
  } else {
    m_currentPartDef = G4ParticleTable::GetParticleTable()->FindParticle(pdgcode);
    if ( !m_currentPartDef && (pdgcode/100000000 == 10)) {
      //Not in ParticleTable and pdgcode is of form 10xxxxxxxx, so look for ion:
      m_currentPartDef = G4IonTable::GetIonTable()->GetIon(pdgcode);
    }
    m_pdg2pdef[pdgcode] = m_currentPartDef;
  }
  return m_currentPartDef;
}
