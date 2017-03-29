#include "G4MCPLWriter.hh"
#include "G4Track.hh"
#include <sstream>

///////////////////////////////////////////////////////////////////////////////////
//                                                                               //
// Implementation of G4MCPLWriter class.                                         //
//                                                                               //
// This file can be freely used as per the terms in the LICENSE file.            //
//                                                                               //
// Written by Thomas Kittelmann, 2016.                                           //
//                                                                               //
///////////////////////////////////////////////////////////////////////////////////

G4MCPLWriter::G4MCPLWriter( const G4String& outputFile,
                            const G4String& name )
  : G4VSensitiveDetector(name),
    m_store_polarisation(false),
    m_store_userflags(false)
{
  std::memset(&m_p,0,sizeof(m_p));
  m_f = mcpl_create_outfile( outputFile.c_str() );

  {
    std::stringstream tmp;
    tmp << "G4MCPLWriter [" << name <<"]";
    mcpl_hdr_set_srcname( m_f, tmp.str().c_str() );
  }

  G4String ufdescr = UserFlagsDescription();
  if (!ufdescr.empty()) {
    std::stringstream tmp;
    tmp << "UserFlagDescription: "<<ufdescr;
    mcpl_hdr_add_comment( m_f, tmp.str().c_str() );
    mcpl_enable_userflags( m_f );
    m_store_userflags = true;
  }
}

G4MCPLWriter::~G4MCPLWriter()
{
  mcpl_closeandgzip_outfile(m_f);
}

G4bool G4MCPLWriter::ProcessHits(G4Step * step,G4TouchableHistory*)
{
  //Only consider particle steps originating at the boundary
  //of the monitored volume:
  if ( step->GetPreStepPoint()->GetStepStatus() != fGeomBoundary )
    return false;

  //Store the state at the beginning of the step, but avoid
  //particles taking their very first step (this would double-
  //count secondary particles created at the volume edge):
  if ( step->GetTrack()->GetCurrentStepNumber() > 1 )
    StorePreStep(step);

  //Tell Geant4 to stop further tracking of the particle:
  Kill(step);
  return true;
}

void G4MCPLWriter::AddComment( const G4String& comment )
{
  mcpl_hdr_add_comment( m_f, comment.c_str() );
}

void G4MCPLWriter::AddData( const G4String& dataKey, size_t dataLength, const char* data )
{
  mcpl_hdr_add_data( m_f, dataKey.c_str(), dataLength, data );
}

void G4MCPLWriter::EnableDoublePrecision()
{
  mcpl_enable_doubleprec(m_f);
}

void G4MCPLWriter::EnablePolarisation()
{
  mcpl_enable_polarisation(m_f);
  m_store_polarisation = true;
}

void G4MCPLWriter::EnableUniversalWeight(G4double w)
{
  mcpl_enable_universal_weight(m_f,w);
}

void G4MCPLWriter::Store( const G4Step * step, const G4StepPoint* pt )
{
  G4Track * trk = step->GetTrack();
  const G4DynamicParticle * dynpar = trk->GetDynamicParticle();
  m_p.pdgcode = dynpar->GetPDGcode();
  if (!m_p.pdgcode&&dynpar->GetParticleDefinition()->GetParticleName()=="opticalphoton") {
    m_p.pdgcode=22;//store optical photons as regular photons
  }

  m_p.time = pt->GetGlobalTime() / CLHEP::millisecond;
  m_p.weight = pt->GetWeight();
  m_p.ekin = pt->GetKineticEnergy();//already in MeV
  const G4ThreeVector& pos = pt->GetPosition();
  const G4ThreeVector& dir = pt->GetMomentumDirection();
  const G4double tocm(1.0/CLHEP::cm);
  m_p.position[0] = pos.x() * tocm;
  m_p.position[1] = pos.y() * tocm;
  m_p.position[2] = pos.z() * tocm;
  m_p.direction[0] = dir.x();
  m_p.direction[1] = dir.y();
  m_p.direction[2] = dir.z();
  G4double dm2 = dir.mag2();
  if (fabs(dm2-1.0)>1.0e-12) {
    if (!dm2) {
      if (m_p.ekin) {
        //inconsistent
        G4Exception("G4MCPLGenerator::GeneratePrimaries()", "G4MCPLWriter01",
                    JustWarning, "Captured particle has no momentum-direction but eKin>0. Choosing momdir (0,0,1).");
      }
      //arguably consistent if ekin=0, but we should in any case only put unit
      //directional vectors in mcpl:
      m_p.direction[0] = m_p.direction[1] = 0.0;
      m_p.direction[2] = 1.0;
    } else {
      //fix normalisation:
      dm2 = 1.0/sqrt(dm2);
      m_p.direction[0] *= dm2;
      m_p.direction[1] *= dm2;
      m_p.direction[2] *= dm2;
    }
  }

  if (m_store_polarisation) {
    const G4ThreeVector& pol = pt->GetPolarization();
    m_p.polarisation[0] = pol.x();
    m_p.polarisation[1] = pol.y();
    m_p.polarisation[2] = pol.z();
  }

  if (m_store_userflags) {
    m_p.userflags = UserFlags(step);
  }

  mcpl_add_particle(m_f,&m_p);

}
