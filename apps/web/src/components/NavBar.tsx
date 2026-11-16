import { NavLink } from "react-router-dom";

const LINKS = [
  { to: "/", label: "Review" },
  { to: "/playbooks", label: "Playbooks" },
  { to: "/search", label: "Search" },
  { to: "/analytics", label: "Analytics" },
  { to: "/about", label: "About" },
];

export function NavBar() {
  return (
    <header style={{ background: "var(--cb-night)", color: "var(--cb-surface)" }}>
      <nav
        style={{
          maxWidth: 1100,
          margin: "0 auto",
          display: "flex",
          alignItems: "center",
          gap: "1.5rem",
          padding: "1rem 1.5rem",
        }}
      >
        <strong style={{ fontFamily: "Newsreader, serif", fontSize: "1.1rem" }}>Clausebook</strong>
        {LINKS.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            style={({ isActive }) => ({
              color: isActive ? "#fff" : "var(--cb-line)",
              textDecoration: "none",
              fontSize: "0.9rem",
            })}
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}
