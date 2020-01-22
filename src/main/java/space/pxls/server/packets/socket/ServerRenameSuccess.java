package space.pxls.server.packets.socket;

public class ServerRenameSuccess {
    public String getNewName() {
        return newName;
    }

    public String type = "rename_success";
    public String newName;

    public ServerRenameSuccess(String newName) {
        this.newName = newName;
    }

    public String getType() {
        return type;
    }
}
