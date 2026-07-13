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
  it("muestra los 6 items de navegacion final", () => {
    render(<Sidebar isOpen={true} isCollapsed={false} onClose={() => {}} />);

    ["Overview", "Bookings", "Conversation", "Cost", "Calls", "Messages"].forEach(
      (label) => {
        expect(screen.getByText(label)).toBeInTheDocument();
      }
    );
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

  it("muestra el badge de no leidos junto a Messages cuando unreadCount > 0", () => {
    render(<Sidebar isOpen={true} isCollapsed={false} onClose={() => {}} unreadCount={3} />);

    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("no muestra badge cuando unreadCount es 0 o no se pasa", () => {
    render(<Sidebar isOpen={true} isCollapsed={false} onClose={() => {}} />);

    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });
});
