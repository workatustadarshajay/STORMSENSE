import React, { Suspense, useEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Canvas, useFrame } from '@react-three/fiber'
import { motion } from 'framer-motion'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import {
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  Check,
  ChevronDown,
  CloudLightning,
  Crosshair,
  Menu,
  MoveRight,
  PackageCheck,
  ShieldCheck,
  Sun,
  Wind,
  X,
} from 'lucide-react'
import * as THREE from 'three'
import './styles.css'

gsap.registerPlugin(ScrollTrigger)

const steps = [
  {
    eyebrow: 'Before the storm',
    title: 'The forecast is clear. The inventory isn’t.',
    description: 'Two stores. The same product. One has too much, one is about to run out.',
    label: 'Regional inventory',
  },
  {
    eyebrow: '24 hours out',
    title: 'A storm is moving in. Demand is moving faster.',
    description: 'Local weather patterns point to a surge in generators, pumps, and tarps.',
    label: 'Storm watch · Gulf Coast',
  },
  {
    eyebrow: 'Ready in minutes',
    title: 'Move what’s already there. Before customers arrive.',
    description: 'StormSense pairs surplus with nearby demand. Your planner approves with one click.',
    label: 'Transfer recommended',
  },
]

function RadarGlobe() {
  const group = useRef(null)
  const cloud = useRef(null)
  const halo = useRef(null)
  const points = useRef(null)
  const positions = new Float32Array(720 * 3)
  let seed = 7
  const random = () => {
    seed = (seed * 16807) % 2147483647
    return (seed - 1) / 2147483646
  }
  for (let i = 0; i < 720; i += 1) {
    const theta = random() * Math.PI * 2
    const phi = Math.acos(2 * random() - 1)
    const radius = 1.55
    positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta)
    positions[i * 3 + 1] = radius * Math.cos(phi)
    positions[i * 3 + 2] = radius * Math.sin(phi) * Math.sin(theta)
  }

  useFrame(({ clock }) => {
    const time = clock.getElapsedTime()
    if (group.current) group.current.rotation.y = time * 0.07
    if (cloud.current) {
      cloud.current.rotation.z = Math.sin(time * 0.22) * 0.08
      cloud.current.scale.setScalar(1 + Math.sin(time * 1.3) * 0.025)
    }
    if (halo.current) halo.current.material.opacity = 0.1 + (Math.sin(time * 1.1) + 1) * 0.045
    if (points.current) points.current.rotation.y = -time * 0.045
  })

  return (
    <group position={[0.25, 0, 0]}>
      <mesh ref={halo} scale={1.48}>
        <sphereGeometry args={[1, 48, 48]} />
        <meshBasicMaterial color="#35d4d0" transparent opacity={0.14} side={THREE.BackSide} />
      </mesh>
      <group ref={group}>
        <mesh>
          <sphereGeometry args={[1.42, 48, 48]} />
          <meshStandardMaterial color="#142a3c" roughness={0.72} metalness={0.12} transparent opacity={0.78} />
        </mesh>
        <mesh scale={1.005}>
          <sphereGeometry args={[1.42, 24, 16]} />
          <meshBasicMaterial color="#8ebfc5" wireframe transparent opacity={0.12} />
        </mesh>
        <points ref={points}>
          <bufferGeometry>
            <bufferAttribute attach="attributes-position" count={720} array={positions} itemSize={3} />
          </bufferGeometry>
          <pointsMaterial color="#84d5d1" size={0.015} transparent opacity={0.52} sizeAttenuation />
        </points>
        <group ref={cloud} position={[0.48, 0.3, 1.02]}>
          <mesh position={[0, 0, 0]}>
            <sphereGeometry args={[0.38, 24, 24]} />
            <meshBasicMaterial color="#ff8069" transparent opacity={0.55} />
          </mesh>
          <mesh position={[-0.24, -0.08, 0.04]}>
            <sphereGeometry args={[0.29, 20, 20]} />
            <meshBasicMaterial color="#ff8069" transparent opacity={0.39} />
          </mesh>
          <mesh position={[0.23, -0.16, -0.04]}>
            <sphereGeometry args={[0.27, 20, 20]} />
            <meshBasicMaterial color="#ffb184" transparent opacity={0.52} />
          </mesh>
          <mesh position={[0.04, -0.37, -0.01]}>
            <sphereGeometry args={[0.12, 12, 12]} />
            <meshBasicMaterial color="#ff876e" transparent opacity={0.75} />
          </mesh>
        </group>
        <mesh position={[0.3, 0.16, 1.13]}>
          <sphereGeometry args={[0.035, 12, 12]} />
          <meshBasicMaterial color="#fff0cd" />
        </mesh>
      </group>
      <mesh rotation={[Math.PI / 2.5, 0.2, 0.15]}>
        <torusGeometry args={[1.83, 0.006, 8, 160]} />
        <meshBasicMaterial color="#6abbb8" transparent opacity={0.32} />
      </mesh>
      <mesh rotation={[Math.PI / 2.5, 0.2, 0.15]}>
        <torusGeometry args={[1.98, 0.002, 6, 160]} />
        <meshBasicMaterial color="#6abbb8" transparent opacity={0.2} />
      </mesh>
    </group>
  )
}

function HeroScene() {
  return (
    <Canvas camera={{ position: [0, 0, 5.4], fov: 38 }} dpr={[1, 1.5]} gl={{ alpha: true, antialias: true }}>
      <ambientLight intensity={0.7} />
      <pointLight position={[3, 2, 4]} intensity={16} color="#4ad8d1" />
      <pointLight position={[-3, -2, 2]} intensity={8} color="#ff8069" />
      <Suspense fallback={null}>
        <RadarGlobe />
      </Suspense>
    </Canvas>
  )
}

function TransferScene({ activeStep, approved, onApprove }) {
  const stormClass = activeStep === 1 ? 'storm-map storm-map--alert' : 'storm-map'
  return (
    <div className={`transfer-scene transfer-scene--${activeStep}`} aria-label="Animated inventory transfer visualization">
      <div className={stormClass}>
        <div className="map-grid" />
        <div className="map-contour contour-one" />
        <div className="map-contour contour-two" />
        <div className="map-contour contour-three" />
        <div className="map-storm"><span /><span /><span /></div>
        <div className="map-tag"><CloudLightning size={13} /> GULF STORM</div>
        <div className="map-node node-north"><span className="node-dot" /><span>STORE 02</span></div>
        <div className="map-node node-south"><span className="node-dot" /><span>STORE 01</span></div>
        <svg className="route-line" viewBox="0 0 500 320" preserveAspectRatio="none" aria-hidden="true">
          <path d="M 332 82 C 315 150 240 154 195 240" />
        </svg>
        <div className="route-pulse" />
      </div>
      <div className="inventory-chip chip-surplus">
        <div className="chip-icon chip-icon--teal"><PackageCheck size={16} /></div>
        <div><span>Store 02 · Surplus</span><strong>+250 <small>units</small></strong></div>
        <span className="chip-status">READY</span>
      </div>
      <div className="inventory-chip chip-demand">
        <div className="chip-icon chip-icon--coral"><Wind size={16} /></div>
        <div><span>Store 01 · Demand</span><strong>250 <small>units</small></strong></div>
        <span className="chip-status chip-status--urgent">URGENT</span>
      </div>
      <button className="transfer-toast" type="button" onClick={onApprove} aria-live="polite" disabled={activeStep !== 2}>
        <span className="toast-check"><Check size={14} /></span><span>{approved ? 'Transfer approved' : 'Approve transfer'}</span><strong>{approved ? 'Just now' : '250 units'}</strong>
      </button>
      <div className="scene-scale">REGION 04 <span>·</span> LIVE MODEL</div>
    </div>
  )
}

function StorySection() {
  const sectionRef = useRef(null)
  const [activeStep, setActiveStep] = useState(0)
  const [approved, setApproved] = useState(false)

  useEffect(() => {
    const context = gsap.context(() => {
      ScrollTrigger.create({
        trigger: sectionRef.current,
        start: 'top top',
        end: 'bottom bottom',
        onUpdate: ({ progress }) => setActiveStep(Math.min(2, Math.floor(progress * 3.01))),
      })
    }, sectionRef)
    return () => context.revert()
  }, [])

  return (
    <section className="story-section" id="platform" ref={sectionRef}>
      <div className="story-pin">
        <div className="story-copy">
          <p className="section-kicker"><span className="kicker-line" /> The moment before the rush</p>
          <div className="story-steps">
            {steps.map((step, index) => (
              <article className={`story-step ${activeStep === index ? 'is-active' : ''}`} key={step.eyebrow} aria-hidden={activeStep !== index}>
                <p className="story-eyebrow">{step.eyebrow}</p>
                <h2>{step.title}</h2>
                <p className="story-description">{step.description}</p>
              </article>
            ))}
          </div>
          <div className="story-progress" aria-label={`Story step ${activeStep + 1} of 3`}>
            {steps.map((step, index) => <span className={activeStep === index ? 'is-current' : ''} key={step.eyebrow} />)}
            <span className="progress-caption">0{activeStep + 1} / 03</span>
          </div>
        </div>
        <div className="story-visual">
          <div className="scene-header"><span className="scene-header-label"><Crosshair size={14} /> {steps[activeStep].label}</span><span className="scene-live"><i /> LIVE</span></div>
          <TransferScene activeStep={activeStep} approved={approved} onApprove={() => setApproved(true)} />
          <div className="scene-footer"><span>WEATHER-DRIVEN DEMAND</span><span>STORMSENSE ENGINE <ArrowUpRight size={12} /></span></div>
        </div>
      </div>
    </section>
  )
}

function Metric({ value, label, detail, icon: Icon, accent }) {
  return (
    <article className="metric-row">
      <div className={`metric-icon metric-icon--${accent}`}><Icon size={19} strokeWidth={1.7} /></div>
      <div className="metric-main"><strong>{value}</strong><span>{label}</span></div>
      <p>{detail}</p>
      <ArrowUpRight className="metric-arrow" size={18} />
    </article>
  )
}

function ROISection() {
  const [stores, setStores] = useState(20)
  const [stockoutLoss, setStockoutLoss] = useState(35)
  const [stockoutReduction, setStockoutReduction] = useState(25)
  const annualImpact = Math.round(stores * stockoutLoss * (stockoutReduction / 100))
  const formattedImpact = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(annualImpact * 1000)

  return (
    <section className="roi-section" id="roi">
      <div className="roi-layout">
        <div className="roi-intro">
          <p className="section-kicker"><span className="kicker-line" /> Make it your numbers</p>
          <h2>What could one better season <em>mean for you?</em></h2>
          <p>Adjust the estimate to match your operation. Your actual results will vary with product mix and local weather.</p>
          <a href="#contact" className="text-link">Talk through your forecast <ArrowRight size={16} /></a>
        </div>
        <div className="roi-tool">
          <div className="roi-controls">
            <label htmlFor="store-count">Stores in your network <strong>{stores}</strong></label>
            <input id="store-count" type="range" min="5" max="50" step="1" value={stores} onChange={(event) => setStores(Number(event.target.value))} style={{ '--range-progress': `${((stores - 5) / 45) * 100}%` }} />
            <div className="range-labels"><span>5 stores</span><span>50 stores</span></div>
            <label htmlFor="loss-estimate">Stockout loss per store <strong>${stockoutLoss}k</strong></label>
            <input id="loss-estimate" type="range" min="10" max="100" step="5" value={stockoutLoss} onChange={(event) => setStockoutLoss(Number(event.target.value))} style={{ '--range-progress': `${((stockoutLoss - 10) / 90) * 100}%` }} />
            <div className="range-labels"><span>$10k</span><span>$100k</span></div>
            <label htmlFor="reduction-estimate">Expected stockout reduction <strong>{stockoutReduction}%</strong></label>
            <input id="reduction-estimate" type="range" min="10" max="40" step="5" value={stockoutReduction} onChange={(event) => setStockoutReduction(Number(event.target.value))} style={{ '--range-progress': `${((stockoutReduction - 10) / 30) * 100}%` }} />
            <div className="range-labels"><span>10%</span><span>40%</span></div>
          </div>
          <div className="roi-result">
            <span className="result-label">Estimated seasonal revenue protected</span>
            <motion.strong key={formattedImpact} initial={{ opacity: 0.35, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.28 }}>{formattedImpact}</motion.strong>
            <div className="result-chart" aria-hidden="true">
              {[30, 46, 39, 59, 52, 70, 63, 86, 72, 100, 91, 118].map((height, index) => <span key={index} style={{ height: `${height}px`, opacity: 0.45 + index * 0.045 }} />)}
            </div>
            <div className="result-caption"><span><i /> Projected opportunity</span><span>PER SEASON</span></div>
          </div>
        </div>
      </div>
      <p className="roi-footnote">Illustrative estimate based on user inputs. Not a guarantee of future revenue.</p>
    </section>
  )
}

function App() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <main>
      <header className="site-header">
        <a href="#top" className="brand" aria-label="StormSense home"><span className="brand-mark"><CloudLightning size={17} fill="currentColor" /></span><span>storm<span>sense</span></span></a>
        <nav className={menuOpen ? 'main-nav is-open' : 'main-nav'} aria-label="Main navigation">
          <a href="#platform" onClick={() => setMenuOpen(false)}>Platform</a>
          <a href="#impact" onClick={() => setMenuOpen(false)}>Impact</a>
          <a href="#roi" onClick={() => setMenuOpen(false)}>ROI calculator</a>
          <a href="#pricing" onClick={() => setMenuOpen(false)}>Pricing</a>
        </nav>
        <a href="#contact" className="header-cta">Book a walkthrough <ArrowUpRight size={15} /></a>
        <button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)} aria-label={menuOpen ? 'Close menu' : 'Open menu'}>{menuOpen ? <X size={21} /> : <Menu size={21} />}</button>
      </header>

      <section className="hero" id="top">
        <div className="hero-grain" />
        <div className="hero-glow" />
        <div className="hero-copy">
          <motion.p className="hero-overline" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.15 }}><span /> WEATHER MOVES FAST. NOW YOUR INVENTORY CAN, TOO.</motion.p>
          <motion.h1 initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.75, delay: 0.28 }}>Be ready before<br />the <span>weather turns.</span></motion.h1>
          <motion.p className="hero-subtitle" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.65, delay: 0.46 }}>Know what customers will need. Move it where it matters. Never miss the storm-driven sale.</motion.p>
          <motion.div className="hero-actions" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.6 }}>
            <a href="#platform" className="button button-primary">See how it works <ArrowDown size={16} /></a>
            <a href="#roi" className="button button-quiet">Estimate your impact <ArrowRight size={16} /></a>
          </motion.div>
          <motion.div className="hero-footnote" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.9 }}><ShieldCheck size={15} /> Built for the decisions that can’t wait</motion.div>
        </div>
        <div className="hero-art" aria-hidden="true"><HeroScene /></div>
        <div className="hero-data hero-data--top"><span className="data-pulse" /> ATLANTIC SYSTEM <strong>ACTIVE</strong></div>
        <div className="hero-data hero-data--bottom"><span>GULF COAST</span><span className="data-divider" /><Sun size={14} /><span>STORM FRONT</span><strong>24h</strong></div>
        <div className="hero-index"><span>01</span><i /><span>04</span></div>
        <a className="scroll-hint" href="#platform"><span>SCROLL TO SEE THE SHIFT</span><ChevronDown size={15} /></a>
      </section>

      <section className="intro-strip" id="impact">
        <p>Weather doesn’t wait<br />for your next planning meeting.</p>
        <div><strong>3–5 <small>days</small></strong><span>Typical manual transfer coordination</span></div>
        <div className="strip-divider" />
        <div><strong>24 <small>hours</small></strong><span>From forecast signal to shelf-ready stock</span></div>
      </section>

      <StorySection />

      <section className="metrics-section">
        <div className="metrics-heading">
          <div><p className="section-kicker"><span className="kicker-line" /> The advantage is in the timing</p><h2>One forecast.<br /><em>Better decisions.</em></h2></div>
          <p>StormSense gives your team the context to act while there’s still time to move product.</p>
        </div>
        <div className="metrics-list">
          <Metric value="24 → 2h" label="From forecast to action" detail="Replace days of coordination with a clear next move." icon={Wind} accent="teal" />
          <Metric value="28%" label="Mean absolute percentage error" detail="Demand forecasts tuned to weather and store history." icon={Crosshair} accent="blue" />
          <Metric value="1 click" label="To approve a transfer" detail="Recommendations your planners can review at a glance." icon={Check} accent="coral" />
          <Metric value="7 days" label="Of demand in view" detail="See the weather-driven need before it reaches your doors." icon={Sun} accent="amber" />
        </div>
        <p className="metrics-note">Forecast accuracy and impact depend on historical data quality, region, and product category.</p>
      </section>

      <section className="workflow-section">
        <div className="workflow-heading"><p className="section-kicker"><span className="kicker-line" /> From signal to shelf</p><h2>A complicated week,<br /><em>made actionable.</em></h2></div>
        <div className="workflow-track">
          <div className="workflow-line" />
          <article className="workflow-step"><span className="workflow-symbol"><CloudLightning size={21} /></span><span className="workflow-time">06:00 · SENSE</span><h3>See the weather shift</h3><p>Local forecasts surface the products likely to move.</p></article>
          <article className="workflow-step"><span className="workflow-symbol"><Crosshair size={21} /></span><span className="workflow-time">06:01 · PREDICT</span><h3>Find the demand gap</h3><p>Store-level needs meet what’s already on hand nearby.</p></article>
          <article className="workflow-step"><span className="workflow-symbol"><MoveRight size={21} /></span><span className="workflow-time">06:04 · RECOMMEND</span><h3>Route the right stock</h3><p>Clear transfer suggestions go to the people who decide.</p></article>
          <article className="workflow-step"><span className="workflow-symbol"><PackageCheck size={21} /></span><span className="workflow-time">ONE CLICK · SERVE</span><h3>Approve. Then get moving.</h3><p>Planners stay in control. Logistics gets a head start.</p></article>
        </div>
      </section>

      <ROISection />

      <section className="pricing-section" id="pricing">
        <div className="pricing-heading"><p className="section-kicker"><span className="kicker-line" /> A better way to plan</p><h2>Built around your<br /><em>store network.</em></h2><p>Start with a conversation. We’ll scope the right fit for your operation.</p></div>
        <div className="pricing-panel">
          <div className="pricing-detail"><span className="pricing-icon"><CloudLightning size={20} /></span><div><h3>StormSense for retail</h3><p>Weather-aware forecasting and transfer recommendations for home improvement teams.</p></div></div>
          <div className="pricing-includes"><span><Check size={14} /> Store-level demand signals</span><span><Check size={14} /> Transfer recommendations</span><span><Check size={14} /> Guided onboarding</span></div>
          <a href="#contact" className="button button-dark">Discuss pricing <ArrowUpRight size={16} /></a>
        </div>
      </section>

      <section className="closing-section" id="contact">
        <div className="closing-orbit" aria-hidden="true"><span /><span /><span /></div>
        <p className="section-kicker"><span className="kicker-line" /> The next storm is already on the way</p>
        <h2>Give your team<br />time to <em>get ahead.</em></h2>
        <p>See how weather-driven planning could work across your stores.</p>
        <a className="button button-primary" href="mailto:hello@stormsense.ai?subject=StormSense%20walkthrough">Book a walkthrough <ArrowUpRight size={16} /></a>
        <span className="closing-note"><ShieldCheck size={14} /> No obligation. Just a clearer forecast.</span>
      </section>

      <footer className="site-footer">
        <a href="#top" className="brand"><span className="brand-mark"><CloudLightning size={17} fill="currentColor" /></span><span>storm<span>sense</span></span></a>
        <span className="footer-copy">Weather-aware inventory planning for home improvement retail.</span>
        <div className="footer-links"><a href="#platform">Platform</a><a href="#roi">ROI calculator</a><a href={`${import.meta.env.BASE_URL}architecture/`}>Architecture</a><a href="mailto:hello@stormsense.ai">Contact</a></div>
        <span className="copyright">© 2026 StormSense</span>
      </footer>
    </main>
  )
}

export default App

createRoot(document.getElementById('root')).render(<App />)