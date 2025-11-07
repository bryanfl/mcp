import { LogOut } from "lucide-react";
import { logoutAction } from "../actions/login";

interface Props {
    title: string;
}

export default function ChatHeader({ title }: Props) {
  return (
    <header className="flex items-center justify-between bg-[#d3052d] px-4 py-3 shadow-md">
      <h1 className="text-lg font-semibold">{title}</h1>
      <div className="text-sm text-white/80"><LogOut className="cursor-pointer" onClick={() => logoutAction()} /></div>
    </header>
  );
}