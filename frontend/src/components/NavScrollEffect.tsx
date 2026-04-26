"use client";
import { useEffect } from "react";

export default function NavScrollEffect() {
  useEffect(() => {
    const nav = document.getElementById("main-nav");
    if (!nav) return;
    const fn = () => nav.classList.toggle("nav-scrolled", window.scrollY > 10);
    window.addEventListener("scroll", fn, { passive: true });
    return () => window.removeEventListener("scroll", fn);
  }, []);
  return null;
}
