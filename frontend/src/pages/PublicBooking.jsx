import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import "./PublicBooking.css";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

const EDITORIAL_PHOTOS = {
  salon: {
    src: "https://images.unsplash.com/photo-1781450090585-1a511b7066d9?auto=format&fit=crop&w=1800&q=85",
    alt: "Bright salon interior with arched mirrors and styling chairs",
    credit: "Barney Goodman",
    href: "https://unsplash.com/photos/a-modern-hair-salon-interior-with-stylish-chairs-and-mirrors-_Fy7Kq0w6OI",
  },
  clinic: {
    src: "https://images.unsplash.com/photo-1776886099265-6366478b341b?auto=format&fit=crop&w=1800&q=85",
    alt: "Quiet, plant-filled wellness waiting room",
    credit: "Amelia Lowell",
    href: "https://unsplash.com/photos/modern-waiting-room-with-white-chairs-and-plants-VBzRklOb7JA",
  },
  restaurant: {
    src: "https://images.unsplash.com/photo-1780397453393-cfc5aac82666?auto=format&fit=crop&w=1800&q=85",
    alt: "Restaurant interior prepared for dining with warm lighting",
    credit: "Grace Anne Bobadilla",
    href: "https://unsplash.com/photos/modern-restaurant-interior-with-tables-chairs-and-warm-lighting-j0dAs1yodko",
  },
};

function resolveWebsiteTheme(business) {
  if (business?.website_style && business.website_style !== "auto") return business.website_style;
  return {
    salon: "editorial",
    clinic: "clinic",
    restaurant: "restaurant",
    sports_turf: "sports",
  }[business?.business_type] || "editorial";
}

function formatTime(value) {
  if (!value) return "";
  const [hours, minutes] = value.split(":").map(Number);
  if (!Number.isFinite(hours) || !Number.isFinite(minutes)) return value;
  return new Date(2000, 0, 1, hours, minutes).toLocaleTimeString([], {
    hour: "numeric",
    minute: minutes ? "2-digit" : undefined,
  });
}

function formatPrice(value) {
  if (value === null || value === undefined || value === "") return null;
  const amount = Number(value);
  if (!Number.isFinite(amount)) return null;
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(amount);
}

function localDateValue() {
  const date = new Date();
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getBusinessTypeLabel(type) {
  return {
    salon: "Salon & beauty",
    clinic: "Health & wellness",
    restaurant: "Dining",
    sports_turf: "Sports & recreation",
  }[type] || "Appointments";
}

function PublicBooking() {
  const { slug } = useParams();
  const [services, setServices] = useState([]);
  const [business, setBusiness] = useState(null);
  const [selectedService, setSelectedService] = useState(null);
  const [selectedDate, setSelectedDate] = useState("");
  const [slots, setSlots] = useState([]);
  const [selectedSlot, setSelectedSlot] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingError, setBookingError] = useState("");
  const [bookingSuccess, setBookingSuccess] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [error, setError] = useState("");
  const [slotError, setSlotError] = useState("");
  const [heroImageFailed, setHeroImageFailed] = useState(false);

  useEffect(() => {
    let isCurrent = true;
    async function loadBusiness() {
      try {
        setLoading(true);
        setError("");
        const [servicesResponse, businessResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/api/book/${slug}/services/`),
          fetch(`${API_BASE_URL}/api/tenants/public/${slug}/`),
        ]);
        const [servicesData, businessData] = await Promise.all([
          servicesResponse.json(),
          businessResponse.json(),
        ]);
        if (!servicesResponse.ok) throw new Error(servicesData.detail || "Unable to load this business’s services.");
        if (!businessResponse.ok) throw new Error(businessData.detail || "Unable to load this business.");
        if (!isCurrent) return;
        setBusiness(businessData);
        setServices(servicesData.results || servicesData);
        setHeroImageFailed(false);
      } catch (loadError) {
        if (isCurrent) setError(loadError.message || "Unable to load this booking page.");
      } finally {
        if (isCurrent) setLoading(false);
      }
    }
    loadBusiness();
    return () => { isCurrent = false; };
  }, [slug]);

  useEffect(() => {
    if (!selectedService || !selectedDate) {
      setSlots([]);
      setSelectedSlot("");
      return undefined;
    }
    let isCurrent = true;
    async function loadAvailableSlots() {
      try {
        setLoadingSlots(true);
        setSlotError("");
        setSlots([]);
        setSelectedSlot("");
        const response = await fetch(
          `${API_BASE_URL}/api/book/${slug}/available-slots/?date=${encodeURIComponent(selectedDate)}&service=${selectedService.id}`
        );
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Unable to load available times.");
        if (isCurrent) setSlots(data.available_slots || []);
      } catch (loadError) {
        if (isCurrent) setSlotError(loadError.message || "Unable to load available times.");
      } finally {
        if (isCurrent) setLoadingSlots(false);
      }
    }
    loadAvailableSlots();
    return () => { isCurrent = false; };
  }, [slug, selectedService, selectedDate]);

  const theme = resolveWebsiteTheme(business);
  const businessName = business?.business_name || slug.replace(/-/g, " ");
  const photo = EDITORIAL_PHOTOS[business?.business_type] || null;
  const businessHours = useMemo(() => {
    const records = new Map((business?.business_hours || []).map((item) => [item.day_of_week, item]));
    return DAYS.map((day, index) => {
      const record = records.get(index);
      return record && !record.is_closed
        ? { day, text: `${formatTime(record.opening_time)} – ${formatTime(record.closing_time)}` }
        : { day, text: "Closed" };
    });
  }, [business?.business_hours]);
  const hasBusinessHours = (business?.business_hours || []).length > 0;

  const jumpTo = (id) => document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  const chooseService = (service) => {
    setSelectedService(service);
    setSelectedDate("");
    setSelectedSlot("");
    setBookingError("");
    setBookingSuccess(null);
    window.setTimeout(() => jumpTo("appointment"), 60);
  };

  const handleBooking = async (event) => {
    event.preventDefault();
    setBookingError("");
    if (!customerName.trim()) return setBookingError("Please enter your name.");
    if (!customerPhone.trim()) return setBookingError("Please enter your phone number.");
    if (!selectedService || !selectedDate || !selectedSlot) return setBookingError("Choose a service, date, and available time to continue.");
    try {
      setBookingLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/book/${slug}/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_name: customerName.trim(),
          customer_phone: customerPhone.trim(),
          booking_date: selectedDate,
          booking_time: selectedSlot,
          service: selectedService.id,
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || data.error || "Unable to create booking.");
      setBookingSuccess(data);
      jumpTo("appointment");
    } catch (bookingSubmitError) {
      setBookingError(bookingSubmitError.message || "Unable to create booking.");
    } finally {
      setBookingLoading(false);
    }
  };

  if (loading) {
    return <main className="public-booking public-state-page" data-theme={theme} aria-live="polite">
      <div className="public-state-brand">BookForge</div>
      <div className="public-loading-mark" aria-hidden="true" />
      <p>Preparing the booking experience…</p>
    </main>;
  }

  if (error) {
    return <main className="public-booking public-state-page" data-theme={theme}>
      <div className="public-state-brand">BookForge</div>
      <div className="public-state-card" role="alert">
        <span className="public-eyebrow">BOOKING PAGE</span>
        <h1>This page is unavailable</h1>
        <p>{error}</p>
        <button type="button" className="editorial-button" onClick={() => window.location.reload()}>Try again</button>
      </div>
    </main>;
  }

  return (
    <main className="public-booking" data-theme={theme}>
      <a className="skip-link" href="#main-content">Skip to content</a>
      <nav className="public-nav" aria-label="Main navigation">
        <a className="public-brand" href="#home" aria-label={`${businessName}, home`}>
          <span className="brand-mark" aria-hidden="true">{businessName.charAt(0)}</span>
          <span>{businessName}</span>
        </a>
        <div className="public-nav-links">
          <a href="#home">Home</a>
          <a href="#services">Services</a>
          <a href="#about">About</a>
          <a href="#contact">Contact</a>
        </div>
        <button className="editorial-button nav-book-button" type="button" onClick={() => jumpTo("services")}>Book an appointment <span aria-hidden="true">↗</span></button>
      </nav>

      <div id="main-content">
        <section className="editorial-hero" id="home" aria-labelledby="business-title">
          <div className="editorial-hero-copy">
            <p className="public-eyebrow">{getBusinessTypeLabel(business?.business_type)}{business?.location ? ` · ${business.location}` : ""}</p>
            <h1 id="business-title">A little time,<br /><em>well spent.</em></h1>
            <p className="editorial-lede">Explore the services at {businessName}, then choose a date and time that works for you.</p>
            <button className="editorial-button" type="button" onClick={() => jumpTo("services")}>Discover services <span aria-hidden="true">↓</span></button>
            <div className="hero-note"><span className="hero-note-rule" />Appointments, at your pace</div>
          </div>
          <div className={`editorial-hero-image ${heroImageFailed || !photo ? "has-fallback" : ""}`}>
            {photo && !heroImageFailed ? <img src={photo.src} alt={photo.alt} fetchPriority="high" onError={() => setHeroImageFailed(true)} /> : <div className="hero-image-fallback" aria-hidden="true"><span>{business?.business_type === "clinic" ? "A considered space for your visit" : business?.business_type === "restaurant" ? "A table, made for you" : "Make room for a little care"}</span></div>}
            {photo && !heroImageFailed && <a className="photo-credit" href={photo.href} target="_blank" rel="noreferrer">Photo by {photo.credit} · Unsplash</a>}
            <div className="hero-image-caption"><span>01</span><span>{business?.location || getBusinessTypeLabel(business?.business_type)}</span></div>
          </div>
          <div className="hero-side-label" aria-hidden="true">A more personal kind of booking</div>
        </section>

        <div className="editorial-divider" aria-hidden="true"><span />A moment for yourself<span /></div>

        <section className="editorial-section services-section" id="services" aria-labelledby="services-title">
          <div className="section-heading">
            <div><p className="public-eyebrow">THE MENU</p><h2 id="services-title">Choose your <em>experience</em></h2></div>
            <p>Find the service that feels right, then select a time from the live availability.</p>
          </div>
          {services.length === 0 ? <div className="empty-services"><span className="empty-service-mark" aria-hidden="true">✳</span><h3>No services are available right now</h3><p>Please contact {businessName} for more information.</p></div> : (
            <div className="editorial-service-list">
              {services.map((service, index) => {
                const price = formatPrice(service.price);
                return <article className={`editorial-service ${selectedService?.id === service.id ? "is-selected" : ""}`} key={service.id}>
                  <span className="service-index">{String(index + 1).padStart(2, "0")}</span>
                  <div className="service-copy">
                    <h3>{service.name}</h3>
                    {service.description && <p>{service.description}</p>}
                    <div className="service-meta">
                      {service.duration ? <span>{service.duration} minutes</span> : null}
                      {price ? <span>{price}</span> : null}
                    </div>
                  </div>
                  <button className="service-select" type="button" aria-pressed={selectedService?.id === service.id} onClick={() => chooseService(service)}>
                    {selectedService?.id === service.id ? "Selected" : "Select service"}<span aria-hidden="true">↗</span>
                  </button>
                </article>;
              })}
            </div>
          )}
        </section>

        <section className="about-band" id="about" aria-labelledby="about-title">
          <div className="about-ornament" aria-hidden="true"><span>✳</span></div>
          <div className="about-copy">
            <p className="public-eyebrow">A NOTE BEFORE YOU VISIT</p>
            <h2 id="about-title">Good things begin<br />with a little <em>space.</em></h2>
            <p>Browse the services available at {businessName}, then reserve an appointment using the live schedule. Service details and availability shown here come from the business’s current booking information.</p>
            {business?.location && <p className="about-location">{business.location}</p>}
          </div>
          <div className="about-detail-card">
            <span className="detail-card-number">01 / 02</span>
            <div className="detail-card-art" aria-hidden="true"><span /><i /><b /></div>
            <p>{getBusinessTypeLabel(business?.business_type)}</p>
          </div>
        </section>

        <section className="appointment-section" id="appointment" aria-labelledby="appointment-title">
          <div className="appointment-intro">
            <p className="public-eyebrow">YOUR VISIT</p>
            <h2 id="appointment-title">Make it <em>yours.</em></h2>
            <p>Select a service, date, and available time. Your booking is submitted directly to {businessName}.</p>
            <ol className="booking-steps" aria-label="Booking progress">
              <li className={selectedService ? "step-done" : "step-current"}>Service</li>
              <li className={selectedDate ? "step-done" : selectedService ? "step-current" : ""}>Date</li>
              <li className={selectedSlot ? "step-done" : selectedDate ? "step-current" : ""}>Time</li>
              <li className={customerName && customerPhone ? "step-done" : selectedSlot ? "step-current" : ""}>Details</li>
            </ol>
          </div>
          <div className="appointment-panel">
            {bookingSuccess ? <div className="booking-confirmation" role="status" aria-live="polite">
              <span className="confirmation-seal" aria-hidden="true">✓</span>
              <p className="public-eyebrow">IT’S CONFIRMED</p>
              <h3>Your time is <em>reserved.</em></h3>
              <p className="confirmation-message">Your booking has been successfully created.</p>
              <dl className="confirmation-details">
                <div><dt>Service</dt><dd>{selectedService?.name}</dd></div>
                <div><dt>Date</dt><dd>{selectedDate}</dd></div>
                <div><dt>Time</dt><dd>{selectedSlot}</dd></div>
                <div><dt>Name</dt><dd>{customerName}</dd></div>
                {bookingSuccess.resource && <div><dt>Reserved</dt><dd>{typeof bookingSuccess.resource === "object" ? bookingSuccess.resource.name : bookingSuccess.resource}</dd></div>}
              </dl>
              <p className="confirmation-note">A confirmation has been recorded for this booking.</p>
            </div> : <>
              {!selectedService && <div className="booking-empty-state"><span>First</span><p>Choose a service above to begin your booking.</p></div>}
              {selectedService && <>
                <div className="selected-service-summary">
                  <div><span className="summary-label">SELECTED SERVICE</span><strong>{selectedService.name}</strong></div>
                  <button type="button" onClick={() => { setSelectedService(null); setSelectedDate(""); setSelectedSlot(""); }}>Change</button>
                </div>
                <div className="date-field">
                  <label htmlFor="booking-date">Choose a date</label>
                  <input id="booking-date" type="date" value={selectedDate} min={localDateValue()} max={new Date(Date.now() + 30 * 86400000).toLocaleDateString("en-CA")} onChange={(event) => { setSelectedDate(event.target.value); setSelectedSlot(""); setBookingError(""); }} />
                  <small>Availability is shown for the next 30 days.</small>
                </div>
              </>}
              {selectedService && selectedDate && <div className="time-field" aria-live="polite">
                <div className="field-heading"><h3>Available times</h3>{!loadingSlots && slots.length > 0 && <span>{slots.length} times</span>}</div>
                {loadingSlots && <p className="inline-state">Finding available times…</p>}
                {slotError && <p className="booking-error" role="alert">{slotError}</p>}
                {!loadingSlots && !slotError && slots.length === 0 && <p className="inline-state">No times are available for this date. Try another day.</p>}
                {!loadingSlots && slots.length > 0 && <div className="editorial-slots">
                  {slots.map((slot) => <button key={slot} type="button" className={selectedSlot === slot ? "slot-choice is-selected" : "slot-choice"} aria-pressed={selectedSlot === slot} onClick={() => { setSelectedSlot(slot); setBookingError(""); }}>{slot}</button>)}
                </div>}
              </div>}
              {selectedSlot && <form className="customer-details" onSubmit={handleBooking}>
                <div className="field-heading"><h3>Your details</h3><span>Almost there</span></div>
                <label htmlFor="customer-name">Full name<input id="customer-name" name="name" type="text" autoComplete="name" value={customerName} onChange={(event) => setCustomerName(event.target.value)} required /></label>
                <label htmlFor="customer-phone">Phone number<input id="customer-phone" name="tel" type="tel" autoComplete="tel" value={customerPhone} onChange={(event) => setCustomerPhone(event.target.value)} required /></label>
                <div className="booking-recap"><span>{selectedService.name}</span><span>{new Date(`${selectedDate}T12:00:00`).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })} · {selectedSlot}</span>{formatPrice(selectedService.price) && <strong>{formatPrice(selectedService.price)}</strong>}</div>
                {bookingError && <p className="booking-error" role="alert">{bookingError}</p>}
                <button className="editorial-button submit-booking" type="submit" disabled={bookingLoading}>{bookingLoading ? "Reserving your time…" : "Confirm appointment"}<span aria-hidden="true">↗</span></button>
                <p className="form-privacy-note">Your details are used to manage this appointment.</p>
              </form>}
            </>}
          </div>
        </section>

        <section className="visit-section" id="contact" aria-labelledby="visit-title">
          <div className="visit-heading"><p className="public-eyebrow">PLAN YOUR VISIT</p><h2 id="visit-title">We’ll be <em>here.</em></h2></div>
          <div className="visit-info">
            {business?.location && <div className="visit-card"><span className="visit-icon" aria-hidden="true">01</span><div><h3>Find us</h3><address>{business.location}</address></div></div>}
            {(business?.contact_phone || business?.contact_email) && <div className="visit-card"><span className="visit-icon" aria-hidden="true">02</span><div><h3>Get in touch</h3>{business.contact_phone && <a href={`tel:${business.contact_phone}`}>{business.contact_phone}</a>}{business.contact_email && <a href={`mailto:${business.contact_email}`}>{business.contact_email}</a>}</div></div>}
            {hasBusinessHours && <div className="visit-card visit-hours-card"><span className="visit-icon" aria-hidden="true">03</span><div><h3>Opening hours</h3><dl className="opening-hours">{businessHours.map(({ day, text }) => <div key={day}><dt>{day}</dt><dd>{text}</dd></div>)}</dl></div></div>}
            {!business?.location && !business?.contact_phone && !business?.contact_email && !hasBusinessHours && <p className="visit-empty">Business contact and opening-hour details are not available here.</p>}
          </div>
        </section>
      </div>

      <footer className="public-footer">
        <a className="public-brand footer-brand" href="#home"><span className="brand-mark" aria-hidden="true">{businessName.charAt(0)}</span><span>{businessName}</span></a>
        <p>{getBusinessTypeLabel(business?.business_type)} · Online appointments</p>
        <div className="footer-links"><a href="#services">Services</a><a href="#about">About</a><a href="#contact">Contact</a>{business?.contact_phone && <a href={`tel:${business.contact_phone}`}>Call</a>}</div>
        <a className="back-to-top" href="#home">Back to top ↑</a>
      </footer>
    </main>
  );
}

export default PublicBooking;
