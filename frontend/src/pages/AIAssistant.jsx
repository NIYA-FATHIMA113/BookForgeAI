import { useState } from "react";

function AIAssistant() {
  const [businessName, setBusinessName] = useState("");

  return (
    <div>
      <h1>Create Your Business with AI</h1>

      <p>
        Tell BookForge AI about your business,
        and we'll help you configure your booking platform.
      </p>

      <div>
        <label>
          What is your business name?
        </label>

        <input
          type="text"
          value={businessName}
          onChange={(e) =>
            setBusinessName(e.target.value)
          }
          placeholder="Enter your business name"
        />
      </div>
    </div>
  );
}

export default AIAssistant;