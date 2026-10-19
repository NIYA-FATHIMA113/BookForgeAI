import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiRequest } from "../services/api";
import ReactMarkdown from "react-markdown";

function AISetup() {
  const navigate = useNavigate();

  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [showPreview, setShowPreview] = useState(false);
  const [websiteStyle, setWebsiteStyle] = useState("auto");

 
  const [business, setBusiness] = useState({
    name: "",
    type: "",
    location: "",
    phone: "",
    email: "",
  });
  const [conversationId, setConversationId] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [services, setServices] = useState([]);
  const [resources, setResources] = useState([]);
  const previewTheme = websiteStyle === "auto"
    ? ({ sports_turf: "bold", salon: "elegant", clinic: "modern", restaurant: "warm" }[business.type] || "nature")
    : websiteStyle;

  const [hours, setHours] = useState({
    days: "",
    opening: "",
    closing: "",
    sundayClosed: false,
  });

  const [bookingRules, setBookingRules] = useState({
    deposit: "",
    bookingLength: "",
  });


 async function handleSend(e) {
  e.preventDefault();

  if (!message.trim() || aiLoading) {
    return;
  }

  const userMessage = message.trim();

  setMessages((current) => [
    ...current,
    {
      role: "user",
      text: userMessage,
    },
  ]);

  setMessage("");
  setAiLoading(true);

  try {
    const data = await apiRequest("/api/ai/chat/", {
      method: "POST",

      body: JSON.stringify({
        message: userMessage,

        ...(conversationId
          ? {
              conversation_id: conversationId,
            }
          : {}),
      }),
    });

    console.log("AI RESPONSE:", data);

    // Save conversation ID returned by Django
    setConversationId(data.conversation_id);

    // Display real AI response
    setMessages((current) => [
      ...current,
      {
        role: "assistant",
        text: data.message,
      },
    ]);

    // Update preview data from real configuration
    if (data.business_configuration) {
      const config = data.business_configuration;

      setBusiness((current) => ({
        ...current,
        name:
          config.business_name ||
          current.name,
        type:
          config.business_type ||
          current.type,
        location:
          config.location ||
          current.location,
        phone:
          config.contact_phone ||
          current.phone,
        email:
          config.contact_email ||
          current.email,
      }));

      if (config.services) {
        setServices(config.services.map((service, index) => ({
          id: service.id || index + 1,
          name: service.name,
          duration: service.duration_minutes || 60,
          price: service.price ?? 0,
        })));
      }

      if (
        config.opening_time ||
        config.closing_time ||
        config.working_days
      ) {
        setHours((current) => ({
          ...current,
          opening:
            config.opening_time?.slice(0, 5) ||
            current.opening,
          closing:
            config.closing_time?.slice(0, 5) ||
            current.closing,
          days:
            config.working_days?.join(
              ", "
            ) ||
            current.days,
        }));
      }

      if (config.number_of_resources) {
        setResources(
          Array.from(
            {
              length:
                config.number_of_resources,
            },
            (_, index) => ({
              id: index + 1,
              name: `Resource ${index + 1}`,
            })
          )
        );
      }
      setBookingRules({
        deposit: config.booking_deposit ?? "No deposit",
        bookingLength: config.booking_length_minutes ?? "",
      });

      // Show preview when the AI has completed the setup.
// Supports both the backend completion flag and the
// final confirmation message from the AI.

const completionMessage =
  data.message?.toLowerCase() || "";

const setupComplete =
  config.configuration_status?.is_complete === true ||
  config.is_complete === true ||
  data.is_complete === true ||
  completionMessage.includes("ready for confirmation") ||
  completionMessage.includes("ready to create your business") ||
  completionMessage.includes("all the information needed") ||
  completionMessage.includes("configuration is ready");

if (setupComplete) {
  setShowPreview(true);
}
    }

  } catch (error) {
    console.error(
      "AI chat failed:",
      error
    );

    setMessages((current) => [
      ...current,
      {
        role: "assistant",
        text:
          "Sorry, something went wrong: " +
          error.message,
      },
    ]);

  } finally {
    setAiLoading(false);
  }
}

const handleConfirm = async () => {
  try {
    if (!conversationId) {
      alert("Conversation not found. Please start the AI setup again.");
      return;
    }

    const response = await apiRequest("/api/ai/confirm/", {
      method: "POST",
      body: JSON.stringify({
        conversation_id: conversationId,
        website_style: websiteStyle,
        services: services.map(({ name, duration, price }) => ({
          name: name.trim(),
          duration_minutes: Number(duration),
          price: Number(price),
        })),
      }),
    });

    setConversationId(response.conversation_id);
    console.log("BUSINESS CREATED:", response);

    navigate(`/book/${response.slug}`);

  } catch (error) {
    console.error("Business creation failed:", error);

    alert(
      error.message || "Failed to create business."
    );
  }
};

  function updateService(id, field, value) {
    setServices((current) =>
      current.map((service) =>
        service.id === id
          ? {
              ...service,
              [field]:
                field === "duration" ||
                field === "price"
                  ? Number(value)
                  : value,
            }
          : service
      )
    );
  }

  function addService() {
    setServices((current) => [
      ...current,
      {
        id: Date.now(),
        name: "New Service",
        duration: 30,
        price: 0,
      },
    ]);
  }

  function removeService(id) {
    setServices((current) =>
      current.filter((service) => service.id !== id)
    );
  }

  function addResource() {
    setResources((current) => [
      ...current,
      {
        id: Date.now(),
        name: "New Resource",
      },
    ]);
  }

  function removeResource(id) {
    setResources((current) =>
      current.filter((resource) => resource.id !== id)
    );
  }

  function updateResource(id, value) {
    setResources((current) =>
      current.map((resource) =>
        resource.id === id
          ? {
              ...resource,
              name: value,
            }
          : resource
      )
    );
  }

  function cleanAIText(text) {
    if (!text) return "";

    return text
      .replace(/\\([*_~`])/g, "$1")
      .replace(/\s+(\d+\.)\s+/g, "\n\n$1 ");
  }
  return (
    <div className="ai-setup-page">

      {/* Header */}

      <header className="ai-setup-header">
        <button
          type="button"
          onClick={() => navigate("/dashboard")}
        >
          ← Dashboard
        </button>

        <div>
          <h1>Create Business with AI 🤖</h1>

          <p>
            Build your booking platform with the help
            of BookForge AI.
          </p>
        </div>
      </header>

      {/* Chat */}

      <section className="ai-chat-card">

        <h2>Tell us about your business</h2>

        <div className="ai-messages">

          {messages.length === 0 && (
            <div className="ai-welcome">
              <h3>
                Welcome to BookForge AI 👋
              </h3>

              <p>
                Tell me what kind of business you
                want to create.
              </p>

              <p>
                Example:
              </p>

              <div className="example-message">
                I run a beauty salon offering
                haircuts, facials and hair spa.
              </div>
            </div>
          )}

          {messages.map((item, index) => (
            <div
              key={index}
              className={`ai-message ${item.role}`}
            >
              <strong>
                {item.role === "user"
                  ? "You"
                  : "BookForge AI"}
              </strong>

              {item.role === "assistant" ? (
                <ReactMarkdown>
                  {item.text}
                </ReactMarkdown>
              ) : (
                <p>{item.text}</p>
              )}
            </div>
          ))}

        </div>

        <form
          className="ai-chat-form"
          onSubmit={handleSend}
        >
          <input
            type="text"
            placeholder="Describe your business..."
            value={message}
            onChange={(e) =>
              setMessage(e.target.value)
            }
          />

          <button type="submit">
            Send
          </button>
        </form>

      </section>

      {/* Preview */}

      {showPreview && (
        <section className="setup-preview">

          <div className="preview-header">
            <div>
              <h2>Business Setup</h2>

              <p>
                Review your setup before creating
                your business.
              </p>
            </div>

            <span className="mock-badge">
              Live configuration
            </span>
          </div>

          {/* Business */}

          <div className="preview-card">

            <h3>Business Information</h3>

            <div className="form-grid">

              <label>
                Business Name

                <input
                  readOnly
                  value={business.name}
                  onChange={(e) =>
                    setBusiness({
                      ...business,
                      name: e.target.value,
                    })
                  }
                />
              </label>

              <label>
                Business Type

                <input
                  readOnly
                  value={business.type}
                  onChange={(e) =>
                    setBusiness({
                      ...business,
                      type: e.target.value,
                    })
                  }
                />
              </label>

              <label>
                Location

                <input
                  readOnly
                  value={business.location}
                  onChange={(e) =>
                    setBusiness({
                      ...business,
                      location: e.target.value,
                    })
                  }
                />
              </label>

              <label>
                Phone

                <input
                  readOnly
                  value={business.phone}
                  placeholder="Phone number"
                  onChange={(e) =>
                    setBusiness({
                      ...business,
                      phone: e.target.value,
                    })
                  }
                />
              </label>

            </div>

          </div>

          {/* Services */}

          <div className="preview-card">

            <div className="section-title-row">
              <div>
                <h3>Services</h3>
                <p>
                  Services customers can book.
                </p>
              </div>

              <button
                type="button"
                onClick={addService}
              >
                + Add Service
              </button>
            </div>

            <div className="service-editor">

              {services.map((service) => (
                <div
                  className="service-editor-row"
                  key={service.id}
                >

                  <input
                    value={service.name}
                    aria-label="Service name"
                    onChange={(e) =>
                      updateService(
                        service.id,
                        "name",
                        e.target.value
                      )
                    }
                  />

                  <input
                    type="number"
                    min="1"
                    aria-label="Duration in minutes"
                    value={service.duration}
                    onChange={(e) =>
                      updateService(
                        service.id,
                        "duration",
                        e.target.value
                      )
                    }
                  />

                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    aria-label="Service price in rupees"
                    value={service.price}
                    onChange={(e) =>
                      updateService(
                        service.id,
                        "price",
                        e.target.value
                      )
                    }
                  />

                  <button
                    type="button"
                    onClick={() =>
                      removeService(service.id)
                    }
                  >
                    Remove
                  </button>

                </div>
              ))}

            </div>

            <div className="table-labels">
              <span>Service</span>
              <span>Duration (min)</span>
              <span>Price (₹)</span>
            </div>

          </div>

          {/* Resources */}

          <div className="preview-card">

            <div className="section-title-row">

              <div>
                <h3>Resources</h3>

                <p>
                  Staff, rooms, chairs or other
                  bookable resources.
                </p>
              </div>

              <button
                type="button"
                disabled
                onClick={addResource}
              >
                + Add Resource
              </button>

            </div>

            {resources.map((resource) => (
              <div
                className="resource-editor-row"
                key={resource.id}
              >

                <input
                  readOnly
                  value={resource.name}
                  onChange={(e) =>
                    updateResource(
                      resource.id,
                      e.target.value
                    )
                  }
                />

                <button
                  type="button"
                  disabled
                  onClick={() =>
                    removeResource(resource.id)
                  }
                >
                  Remove
                </button>

              </div>
            ))}

          </div>

          {/* Business Hours */}

          <div className="preview-card">

            <h3>Business Hours</h3>

            <div className="form-grid">

              <label>
                Working Days

                <input
                  readOnly
                  value={hours.days}
                  onChange={(e) =>
                    setHours({
                      ...hours,
                      days: e.target.value,
                    })
                  }
                />
              </label>

              <label>
                Opening Time

                <input
                  readOnly
                  type="time"
                  value={hours.opening}
                  onChange={(e) =>
                    setHours({
                      ...hours,
                      opening: e.target.value,
                    })
                  }
                />
              </label>

              <label>
                Closing Time

                <input
                  readOnly
                  type="time"
                  value={hours.closing}
                  onChange={(e) =>
                    setHours({
                      ...hours,
                      closing: e.target.value,
                    })
                  }
                />
              </label>

            </div>

            <label className="checkbox-label">

              <input
                disabled
                type="checkbox"
                checked={hours.sundayClosed}
                onChange={(e) =>
                  setHours({
                    ...hours,
                    sundayClosed:
                      e.target.checked,
                  })
                }
              />

              Sunday is closed

            </label>

          </div>

          {/* Booking Rules */}

          <div className="preview-card">

            <h3>Booking Rules</h3>

            <div className="form-grid">

              <label>
                Deposit

                <input
                  readOnly
                  value={bookingRules.deposit}
                  onChange={(e) =>
                    setBookingRules({
                      ...bookingRules,
                      deposit: e.target.value,
                    })
                  }
                />
              </label>

              <label>
                Booking Length (minutes)

                <input
                  readOnly
                  value={bookingRules.bookingLength}
                  onChange={(e) =>
                    setBookingRules({
                      ...bookingRules,
                      bookingLength:
                        e.target.value,
                    })
                  }
                />

              </label>

            </div>

          </div>

          {/* Public website style */}

          <div className="preview-card website-style-card">
            <h3>How should your website feel?</h3>
            <p>Choose a look you like, or let BookForge match a polished theme to your business type.</p>
            <div className="website-style-options" role="radiogroup" aria-label="Website style">
              {[
                ["auto", "Choose for me", "A polished look matched to your business."],
                ["modern", "Modern & minimal", "Clean lines and cool, calm tones."],
                ["warm", "Warm & welcoming", "Soft cream and friendly earthy colors."],
                ["bold", "Bold & energetic", "High contrast with a vivid accent."],
                ["elegant", "Elegant & premium", "Deep tones and a refined finish."],
                ["nature", "Natural & relaxed", "Evergreen accents and soft neutrals."],
                ["3d", "3D Motion", "Layered color, depth, and gentle movement."],
                ["illustrated", "Illustrated", "Scenic shapes and a hand-painted feel."],
                ["playful", "Cartoon Pop", "Rounded forms, bright color, and bold outlines."],
              ].map(([value, title, description]) => (
                <label className={`website-style-option ${websiteStyle === value ? "selected" : ""}`} key={value}>
                  <input type="radio" name="website-style" value={value} checked={websiteStyle === value} onChange={() => setWebsiteStyle(value)} />
                  <span className={`style-option-art theme-${value}`} aria-hidden="true"><i /><i /><b /></span>
                  <span className="style-option-copy"><strong>{title}</strong><small>{description}</small></span>
                </label>
              ))}
            </div>
            <div className={`website-style-live-preview theme-${previewTheme}`} aria-live="polite">
              <div className="style-preview-window">
                <div className="style-preview-top"><i /><i /><i /><span>BOOK A VISIT</span></div>
                <div className="style-preview-scene"><small>WELCOME TO</small><strong>{business.name || "Your business"}</strong><span>Find a time that works for you</span><b>Explore services</b></div>
                <div className="style-preview-service"><i /><span><b>{services[0]?.name || "Your service"}</b><small>Choose a service and book online</small></span><em>›</em></div>
              </div>
              <p>Live style preview · {websiteStyle === "auto" ? `Matched to ${business.type || "your business"}` : websiteStyle === "3d" ? "3D Motion" : websiteStyle === "illustrated" ? "Illustrated" : websiteStyle === "playful" ? "Cartoon Pop" : websiteStyle}</p>
            </div>
          </div>

          {/* Confirm */}

          <div className="confirm-section">

        <div>
          <h2>
            Ready to create your business?
          </h2>

          <p>
            Review the information above and
            confirm when everything looks correct.
          </p>
        </div>

        <button
          type="button"
          onClick={handleConfirm}
        >
          Confirm & Create Business
        </button>

      </div>

        </section>
      )}

    </div>
  );
}

export default AISetup;
