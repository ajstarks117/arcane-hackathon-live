import { useState } from "react";
import { Avatar, Badge, Button, Field, Icon, PageHeader, SearchBox, SelectBox, Toggle } from "./ui";

export function ComponentsPage() {
  const [value, setValue] = useState(72);
  return (
    <div className="page component-page">
      <PageHeader
        title="Component library"
        description="Shared ARCANE interface patterns and interaction states."
      />
      <section>
        <h2>Buttons</h2>
        <div className="component-row">
          <Button kind="primary">Primary action</Button>
          <Button>Secondary action</Button>
          <Button kind="ghost">Quiet action</Button>
          <Button kind="danger">Reject fix</Button>
          <Button disabled>Disabled</Button>
          <button className="button primary loading">
            <span className="spinner" />
            Working
          </button>
        </div>
      </section>
      <section>
        <h2>Status and people</h2>
        <div className="component-row">
          <Badge tone="success">Tests passed</Badge>
          <Badge tone="error">Build failed</Badge>
          <Badge tone="saffron">Needs attention</Badge>
          <Badge>Working</Badge>
          {["Priya Nair", "Daniel Okafor", "Mei Lin", "Arjun Rao"].map((n) => (
            <Avatar name={n} key={n} />
          ))}
        </div>
      </section>
      <section>
        <h2>Form controls</h2>
        <div className="form-grid three">
          <Field label="Repository" helper="The codebase ARCANE watches.">
            <input defaultValue="payments-service" />
          </Field>
          <Field label="Branch">
            <SelectBox>main</SelectBox>
          </Field>
          <Field label="GitHub token" helper="Stored encrypted.">
            <div className="secret-input">
              <input type="password" defaultValue="github_secret_token" />
              <button>
                <Icon name="eye" />
              </button>
            </div>
          </Field>
          <Field
            label="Repository with an error"
            error="That repository has no CI workflow. Add one in .github/workflows and try again."
          >
            <input className="has-error" defaultValue="docs-site" />
          </Field>
          <Field label="Protected branches">
            <div className="chip-input">
              <span>
                main <Icon name="x" size={12} />
              </span>
              <input />
            </div>
          </Field>
          <Field label={`Confidence · ${value}%`}>
            <input
              className="range"
              type="range"
              value={value}
              onChange={(e) => setValue(Number(e.target.value))}
            />
          </Field>
        </div>
      </section>
      <section>
        <h2>Selection controls</h2>
        <div className="component-row spread">
          <div className="radio-group">
            <label>
              <input type="radio" name="r" defaultChecked />
              Open a pull request
            </label>
            <label>
              <input type="radio" name="r" />
              Always ask a person
            </label>
          </div>
          <label className="toggle-label">
            <Toggle checked />
            Network off
          </label>
          <div className="segmented">
            <button className="active">Unified</button>
            <button>Split</button>
          </div>
        </div>
      </section>
      <section>
        <h2>Feedback</h2>
        <div className="component-row">
          <div className="inline-alert success">
            <Icon name="check" />
            Connection passed in 420ms.
          </div>
          <div className="inline-alert error">
            <Icon name="info" />
            The API key was rejected. Replace it and test again.
          </div>
          <span className="tooltip-demo">
            Hover for evidence<span>View the test and commit evidence ARCANE used.</span>
          </span>
        </div>
      </section>
    </div>
  );
}
