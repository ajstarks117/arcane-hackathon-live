import React from "react";

export type IconName =
  | "home"
  | "repair"
  | "terminal"
  | "conflict"
  | "pull"
  | "person"
  | "history"
  | "settings"
  | "search"
  | "chevron"
  | "more"
  | "check"
  | "x"
  | "copy"
  | "branch"
  | "github"
  | "bell"
  | "plus"
  | "sliders"
  | "file"
  | "folder"
  | "spark"
  | "command"
  | "external"
  | "eye"
  | "grip"
  | "send"
  | "info"
  | "logout"
  | "shield"
  | "clock"
  | "code";

const paths: Record<IconName, React.JSX.Element> = {
  home: (
    <>
      <path d="M3 10.5 12 3l9 7.5" />
      <path d="M5.5 9v11h13V9M9 20v-6h6v6" />
    </>
  ),
  repair: (
    <>
      <path d="m14.7 6.3 3-3a5 5 0 0 1-6.4 6.4L5.7 15.3a2 2 0 1 0 3 3l5.6-5.6a5 5 0 0 1 6.4-6.4l-3 3" />
    </>
  ),
  terminal: (
    <>
      <path d="m5 7 4 4-4 4M11 17h8" />
      <rect x="2.5" y="3.5" width="19" height="17" rx="2" />
    </>
  ),
  conflict: (
    <>
      <path d="M8 3v4a4 4 0 0 0 4 4v0a4 4 0 0 1 4 4v6M16 3v4a4 4 0 0 1-4 4M13 18l3 3 3-3" />
    </>
  ),
  pull: (
    <>
      <circle cx="6" cy="5" r="2" />
      <circle cx="18" cy="19" r="2" />
      <path d="M6 7v12M18 17V9a4 4 0 0 0-4-4h-2M9 8l3-3-3-3" />
    </>
  ),
  person: (
    <>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21a8 8 0 0 1 16 0" />
    </>
  ),
  history: (
    <>
      <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
      <path d="M3 3v5h5M12 7v5l3 2" />
    </>
  ),
  settings: (
    <>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3A1.7 1.7 0 0 0 10 3v-.2h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-4-4" />
    </>
  ),
  chevron: <path d="m8 10 4 4 4-4" />,
  more: (
    <>
      <circle cx="5" cy="12" r="1" />
      <circle cx="12" cy="12" r="1" />
      <circle cx="19" cy="12" r="1" />
    </>
  ),
  check: <path d="m5 12 4 4L19 6" />,
  x: (
    <>
      <path d="m6 6 12 12M18 6 6 18" />
    </>
  ),
  copy: (
    <>
      <rect x="8" y="8" width="12" height="12" rx="2" />
      <path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3" />
    </>
  ),
  branch: (
    <>
      <circle cx="6" cy="5" r="2" />
      <circle cx="6" cy="19" r="2" />
      <circle cx="18" cy="7" r="2" />
      <path d="M6 7v10M8 15c5 0 3-8 8-8" />
    </>
  ),
  github: (
    <>
      <path d="M12 2.8a9.4 9.4 0 0 0-3 18.3v-2.3c-2.4.5-2.9-1-2.9-1-.4-1-.9-1.3-.9-1.3-.8-.5 0-.5 0-.5.8 0 1.3.9 1.3.9.7 1.3 2 1 2.5.8.1-.6.3-1 .5-1.2-1.9-.2-3.8-.9-3.8-4.2 0-.9.3-1.7.9-2.3-.1-.2-.4-1.1.1-2.3 0 0 .7-.2 2.4.9a8.2 8.2 0 0 1 4.4 0c1.7-1.1 2.4-.9 2.4-.9.5 1.2.2 2.1.1 2.3.6.6.9 1.4.9 2.3 0 3.3-2 4-3.9 4.2.3.3.6.8.6 1.6v3a9.4 9.4 0 0 0-3-18.3Z" />
    </>
  ),
  bell: (
    <>
      <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" />
    </>
  ),
  plus: <path d="M12 5v14M5 12h14" />,
  sliders: (
    <>
      <path d="M4 6h10M18 6h2M4 12h2M10 12h10M4 18h7M15 18h5" />
      <circle cx="16" cy="6" r="2" />
      <circle cx="8" cy="12" r="2" />
      <circle cx="13" cy="18" r="2" />
    </>
  ),
  file: (
    <>
      <path d="M5 3h9l5 5v13H5Z" />
      <path d="M14 3v5h5" />
    </>
  ),
  folder: <path d="M3 6h7l2 2h9v11H3Z" />,
  spark: (
    <>
      <path d="m12 3 1.3 4.7L18 9l-4.7 1.3L12 15l-1.3-4.7L6 9l4.7-1.3ZM19 15l.7 2.3L22 18l-2.3.7L19 21l-.7-2.3L16 18l2.3-.7Z" />
    </>
  ),
  command: (
    <>
      <path d="M9 6v12M15 6v12M6 9h12M6 15h12" />
      <path d="M9 6a3 3 0 1 0-3 3M15 6a3 3 0 1 1 3 3M9 18a3 3 0 1 1-3-3M15 18a3 3 0 1 0 3-3" />
    </>
  ),
  external: (
    <>
      <path d="M14 4h6v6M20 4l-9 9" />
      <path d="M18 13v7H4V6h7" />
    </>
  ),
  eye: (
    <>
      <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z" />
      <circle cx="12" cy="12" r="2.5" />
    </>
  ),
  grip: (
    <>
      <circle cx="9" cy="7" r="1" />
      <circle cx="15" cy="7" r="1" />
      <circle cx="9" cy="12" r="1" />
      <circle cx="15" cy="12" r="1" />
      <circle cx="9" cy="17" r="1" />
      <circle cx="15" cy="17" r="1" />
    </>
  ),
  send: (
    <>
      <path d="m3 3 18 9-18 9 4-9Z" />
      <path d="M7 12h14" />
    </>
  ),
  info: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v6M12 7h.01" />
    </>
  ),
  logout: (
    <>
      <path d="M10 4H4v16h6M14 8l4 4-4 4M8 12h10" />
    </>
  ),
  shield: (
    <>
      <path d="M12 3 5 6v5c0 4.5 3 8.2 7 10 4-1.8 7-5.5 7-10V6Z" />
      <path d="m9 12 2 2 4-4" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>
  ),
  code: (
    <>
      <path d="m8 9-3 3 3 3M16 9l3 3-3 3M14 5l-4 14" />
    </>
  ),
};

export function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
  return (
    <svg
      className="icon"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      {paths[name]}
    </svg>
  );
}

export function Mark() {
  return (
    <svg width="27" height="18" viewBox="0 0 27 18" fill="none" aria-hidden>
      <path d="M1 9h8" stroke="#1B2622" strokeWidth="2" />
      <path d="M18 9h8" stroke="#1B2622" strokeWidth="2" />
      <path d="m9 9 3-4 3 8 3-4" stroke="#D49A1A" strokeWidth="2" strokeLinejoin="round" />
    </svg>
  );
}

export function Avatar({ name, small = false }: { name: string; small?: boolean }) {
  const initials = name
    .split(" ")
    .map((v) => v[0])
    .join("")
    .slice(0, 2);
  const tone = ["sage", "sand", "clay", "blue"][name.length % 4];
  return (
    <span className={`avatar ${tone} ${small ? "small" : ""}`} title={name}>
      {initials}
    </span>
  );
}

export function Button({
  children,
  kind = "secondary",
  icon,
  onClick,
  disabled = false,
}: {
  children: React.ReactNode;
  kind?: "primary" | "secondary" | "danger" | "ghost";
  icon?: IconName;
  onClick?: () => void;
  disabled?: boolean;
}) {
  return (
    <button className={`button ${kind}`} onClick={onClick} disabled={disabled}>
      {icon && <Icon name={icon} size={16} />}
      <span>{children}</span>
    </button>
  );
}

export function Field({
  label,
  children,
  helper,
  error,
}: {
  label: string;
  children: React.ReactNode;
  helper?: string;
  error?: string;
}) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      {children}
      {helper && <span className="helper">{helper}</span>}
      {error && (
        <span className="field-error">
          <Icon name="info" size={14} />
          {error}
        </span>
      )}
    </label>
  );
}

export function SelectBox({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <button className={`select-box ${className}`}>
      {children}
      <Icon name="chevron" size={15} />
    </button>
  );
}

export function SearchBox({
  placeholder = "Search",
  value,
  onChange,
  shortcut,
}: {
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  shortcut?: string;
}) {
  return (
    <div className="search-box">
      <Icon name="search" size={17} />
      <input
        aria-label={placeholder}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
      />
      {shortcut && <kbd>{shortcut}</kbd>}
    </div>
  );
}

export function Badge({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: "neutral" | "success" | "error" | "saffron";
}) {
  return (
    <span className={`badge ${tone}`}>
      <span className="status-dot" />
      {children}
    </span>
  );
}

export function Modal({
  title,
  description,
  children,
  onClose,
  footer,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
  onClose: () => void;
  footer: React.ReactNode;
}) {
  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true">
        <div className="modal-head">
          <div>
            <h2>{title}</h2>
            {description && <p>{description}</p>}
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close">
            <Icon name="x" />
          </button>
        </div>
        <div className="modal-body">{children}</div>
        <div className="modal-footer">{footer}</div>
      </div>
    </div>
  );
}

export function Toggle({ checked, onChange }: { checked: boolean; onChange?: (v: boolean) => void }) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      className={`toggle ${checked ? "on" : ""}`}
      onClick={() => onChange?.(!checked)}
    >
      <span />
    </button>
  );
}


export function PageHeader({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="page-header">
      <div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </div>
  );
}

export function Select({
  value,
  options,
  onChange,
  className = "",
}: {
  value: string;
  options: { value: string; label: string }[];
  onChange: (v: string) => void;
  className?: string;
}) {
  const current = options.find((o) => o.value === value)?.label ?? value;
  return (
    <label className={`select-box select-native ${className}`}>
      <span>{current}</span>
      <Icon name="chevron" size={15} />
      <select value={value} onChange={(e) => onChange(e.target.value)} aria-label={current}>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export function Empty({
  title,
  body,
  action,
}: {
  title: string;
  body: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="empty-state">
      <Icon name="spark" size={22} />
      <strong>{title}</strong>
      <p>{body}</p>
      {action}
    </div>
  );
}
