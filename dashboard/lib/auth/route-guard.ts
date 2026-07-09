const PUBLIC_PATHS = ["/login", "/api/login"];

export function isPublicPath(pathname: string): boolean {
  if (pathname.startsWith("/_next")) {
    return true;
  }

  return PUBLIC_PATHS.some((publicPath) => {
    return pathname === publicPath || pathname.startsWith(`${publicPath}/`);
  });
}
