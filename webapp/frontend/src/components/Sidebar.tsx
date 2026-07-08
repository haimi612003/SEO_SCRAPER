import type { Nav } from "../types";

interface SidebarProps {
  nav: Nav;
  onNav: (nav: Nav) => void;
  onOpenSettings: () => void;
}

export default function Sidebar({ nav, onNav, onOpenSettings }: SidebarProps) {
  return (
    <div className="sidebar">
      <div className="brand">
        <div className="brand-icon"></div>
        <div>
          <div className="brand-name">SERP Scraper</div>
          <div className="brand-sub">Excel export tool</div>
        </div>
      </div>
      <nav className="nav">
        <div className={"nav-item" + (nav === "new" ? " active" : "")} onClick={() => onNav("new")}>
          <span className="nav-dot"></span>
          <span>Công việc mới</span>
        </div>
        <div className={"nav-item" + (nav === "history" ? " active" : "")} onClick={() => onNav("history")}>
          <span className="nav-dot"></span>
          <span>Lịch sử</span>
        </div>
      </nav>
      <div className="spacer"></div>
      <div className="nav-item settings-link" onClick={onOpenSettings}>
        <span className="gear"></span>
        <span>Cài đặt engine / API key</span>
      </div>
      <div className="version">v1.0 · Python 3.9+</div>
    </div>
  );
}
