import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Sidebar } from "./Sidebar";

vi.mock("next/navigation", () => ({
  usePathname: () => "/"
}));

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
    onClick,
    className
  }: {
    children: React.ReactNode;
    href: string;
    onClick?: () => void;
    className?: string;
  }) => (
    <a
      href={href}
      onClick={(event) => {
        event.preventDefault();
        onClick?.();
      }}
      className={className}
    >
      {children}
    </a>
  )
}));

describe("Sidebar", () => {
  it("muestra los items de navegacion visibles, incluyendo Callbacks", () => {
    render(<Sidebar isOpen={true} isCollapsed={false} onClose={() => {}} />);

    ["Overview", "Bookings", "Callbacks", "Conversation", "Cost", "Calls"].forEach((label) => {
      expect(screen.getByText(label)).toBeInTheDocument();
    });
  });

  it("oculta el tab Messages hasta que la feature este terminada", () => {
    render(<Sidebar isOpen={true} isCollapsed={false} onClose={() => {}} />);

    expect(screen.queryByText("Messages")).not.toBeInTheDocument();
  });

  it("llama a onClose al hacer click en un link", () => {
    const onClose = vi.fn();
    render(<Sidebar isOpen={true} isCollapsed={false} onClose={onClose} />);

    fireEvent.click(screen.getByText("Calls"));

    expect(onClose).toHaveBeenCalled();
  });

  it("cuando isOpen es false no tiene la clase de overlay visible", () => {
    render(<Sidebar isOpen={false} isCollapsed={false} onClose={() => {}} />);

    const nav = screen.getByRole("navigation");

    expect(nav.className).toContain("-translate-x-[calc(100%+1rem)]");
  });

  it("no muestra badge de Messages aunque unreadCount > 0 mientras el tab este oculto", () => {
    render(<Sidebar isOpen={true} isCollapsed={false} onClose={() => {}} unreadCount={3} />);

    expect(screen.queryByText("3")).not.toBeInTheDocument();
  });

  it("no muestra badge cuando unreadCount es 0 o no se pasa", () => {
    render(<Sidebar isOpen={true} isCollapsed={false} onClose={() => {}} />);

    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });

  it("muestra el badge de emergencias pendientes junto a Callbacks cuando emergencyPendingCount > 0", () => {
    render(<Sidebar isOpen={true} isCollapsed={false} onClose={() => {}} emergencyPendingCount={2} />);

    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("no muestra badge de emergencias cuando emergencyPendingCount es 0 o no se pasa", () => {
    render(<Sidebar isOpen={true} isCollapsed={false} onClose={() => {}} />);

    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });
});
