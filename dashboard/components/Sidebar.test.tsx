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
  it("muestra los 7 items de navegacion", () => {
    render(<Sidebar isOpen={true} onClose={() => {}} />);

    ["Resumen", "Volumen", "Reservas", "Conversacion", "Costo", "Llamadas", "Mensajes"].forEach(
      (label) => {
        expect(screen.getByText(label)).toBeInTheDocument();
      }
    );
  });

  it("llama a onClose al hacer click en un link", () => {
    const onClose = vi.fn();
    render(<Sidebar isOpen={true} onClose={onClose} />);

    fireEvent.click(screen.getByText("Llamadas"));

    expect(onClose).toHaveBeenCalled();
  });

  it("cuando isOpen es false no tiene la clase de overlay visible", () => {
    render(<Sidebar isOpen={false} onClose={() => {}} />);

    const nav = screen.getByRole("navigation");

    expect(nav.className).toContain("-translate-x-full");
  });

  it("muestra el badge de no leidos junto a Mensajes cuando unreadCount > 0", () => {
    render(<Sidebar isOpen={true} onClose={() => {}} unreadCount={3} />);

    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("no muestra badge cuando unreadCount es 0 o no se pasa", () => {
    render(<Sidebar isOpen={true} onClose={() => {}} />);

    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });
});
