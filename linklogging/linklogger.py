import asyncio
import json

from linkhandlers.instagramlink import InstagramLink
from linkhandlers.tiktoklink import TiktokLink
from linkhandlers.twitterlink import TwitterLink

class LinkLogger:
    def __init__(self):
        self.filepath = "linklogging/log.json"
        self.lock = asyncio.Lock()
        self.data = {}
        self.linkHandlers = [TwitterLink(), InstagramLink(), TiktokLink()]

    async def load(self):
        """
        Load the logger data from the JSON file.
        """
        async with self.lock:
            try:
                with open(self.filepath, "r") as f:
                    self.data = json.load(f)
                print("Log loaded successfully.")
            except FileNotFoundError:
                self.data = {
                    handler.name: {"users": {}, "servers": {}, "links_fixed": 0} for handler in self.linkHandlers
                }
                self.data["ignored"] = {}
                with open(self.filepath, "w") as f:
                    json.dump(self.data, f, indent=4)
                print("Log file was not found, expected 'linklogging/log.json'. A new log file has been created. If this is the first time running, ignore this message.")

    async def dump(self):
        """
        Save the current state of the logger to the JSON file.
        """
        async with self.lock:
            with open(self.filepath, "w") as f:
                json.dump(self.data, f, indent=4)

    async def add_to_server(self, serverID, entryNum, linkName):
        """        
        Add an entry to the server statistics for a specific link type.
        
        Parameters
        ----------
        serverID : str
            The ID of the server.

        entryNum : int
            The number of entries to add for the server.

        linkName : str
            The name of the platform associated with the link (e.g., "twitter", "instagram").
        """
        serverID = str(serverID)
        async with self.lock:
            if serverID not in self.data[linkName]["servers"]:
                self.data[linkName]["servers"][serverID] = 0
            self.data[linkName]["servers"][serverID] += entryNum

    async def add_to_user(self, userID, entryNum, linkName):
        """        
        Add an entry to the user statistics for a specific link type.
        
        Parameters
        ----------
        userID : str
            The ID of the user.

        entryNum : int
            The number of entries to add for the user.

        linkName : str
            The name of the platform associated with the link (e.g., "twitter", "instagram").
        """
        userID = str(userID)
        async with self.lock:
            if userID not in self.data[linkName]["users"]:
                self.data[linkName]["users"][userID] = 0
            self.data[linkName]["users"][userID] += entryNum

    async def add_total_fixed(self, entryNum, linkName):
        """
        Add to the total number of fixed links for a specific link type.
        
        Parameters
        ----------
        entryNum : int
            The number of entries to add to the total fixed count.

        linkName : str
            The name of the platform associated with the link (e.g., "twitter", "instagram").
        """
        async with self.lock:
            self.data[linkName]["links_fixed"] += entryNum

    async def add_ignored(self, userID):
        """
        Add a user to the ignored notifications list.

        Parameters
        ----------
        userID : str
            The ID of the user.

        Returns
        -------
        bool
            True if the user was successfully added, False if they were already in the list.
        """
        userID = str(userID)
        async with self.lock:
            if userID not in self.data["ignored"]:
                self.data["ignored"][userID] = True
                return True
            return False

    async def rem_ignored(self, userID):
        """
        Remove a user from the ignored notifications list.
        
        Parameters
        ----------
        userID : str
            The ID of the user.

        Returns
        -------
        bool
            True if the user was successfully removed, False if they were not in the list.
        """
        userID = str(userID)
        async with self.lock:
            if userID in self.data["ignored"]:
                self.data["ignored"].pop(userID, None)
                return True
            return False

    async def get_global_stats(self):
        """Get global statistics for all links fixed."""
        async with self.lock:
            # Make a copy of the data while holding the lock
            data_snapshot = self.data.copy()
        
        # Calculate statistics using the snapshot (outside the lock)
        server_totals = {}
        user_totals = {}
        total_links_fixed = 0
        
        for linkName in data_snapshot:
            if linkName == "ignored":
                continue
            link_data = data_snapshot[linkName]
            # Add to total links fixed
            total_links_fixed += link_data.get('links_fixed', 0)
            # Aggregate server stats
            for server_id, count in link_data.get("servers", {}).items():
                server_totals[server_id] = server_totals.get(server_id, 0) + count
            # Aggregate user stats
            for user_id, count in link_data.get("users", {}).items():
                user_totals[user_id] = user_totals.get(user_id, 0) + count

        top_servers = sorted(server_totals.items(), key=lambda x: x[1], reverse=True)
        top_users = sorted(user_totals.items(), key=lambda x: x[1], reverse=True)

        return {
            'total_links_fixed': total_links_fixed,
            'top_servers': top_servers,
            'top_users': top_users
        }

    async def get_all_server_stats(self, serverID):
        """
        Get the total number of entries for a specific server across all link types.
        
        Parameters
        ----------
        serverID : str
            The ID of the server.
        Returns
        -------
        int
            The total number of entries for the server across all link types.
        """
        count = 0
        for handler in self.linkHandlers:
            linkName = handler.name
            serverID = str(serverID)
            async with self.lock:
                if serverID not in self.data[linkName]["servers"]:
                    pass
                else:
                    count += self.data[linkName]["servers"][serverID]
        return count

    async def get_all_user_stats(self, userID):
        """
        Get the total number of entries for a specific user across all link types.

        Parameters
        ----------
        userID : str
            The ID of the user.
        Returns
        -------
        int
            The total number of entries for the user across all link types.
        """
        count = 0
        for handler in self.linkHandlers:
            linkName = handler.name
            userID = str(userID)
            async with self.lock:
                if userID not in self.data[linkName]["users"]:
                    pass
                else:
                    count += self.data[linkName]["users"][userID]
        return count
    
    async def get_total_fixed(self):
        """
        Get the total number of links fixed across all users and servers.

        Returns
        -------
        int
            The total number of links fixed.
        """
        total = 0
        for handler in self.linkHandlers:
            linkName = handler.name
            async with self.lock:
                total += self.data[linkName]['links_fixed']
        return total

    async def get_ignored(self, userID):
        """
        Check if a user is in the ignored notifications list.

        Parameters
        ----------
        userID : str
            The ID of the user.

        Returns
        -------
        bool
            True if the user is in the ignored list, False otherwise.
        """
        userID = str(userID)
        async with self.lock:
            if userID not in self.data["ignored"]:
                return False
            return True

    async def update(self, serverID, userID, entryNum, linkName):
        """
        Update the logger with a new entry for both server and user statistics.
        
        Parameters
        ----------
        serverID : str
            The ID of the server.

        userID : str
            The ID of the user.

        entryNum : int
            The number of entries to add for the user.

        linkName : str
            The name of the platform associated with the link (e.g., "twitter", "instagram").
        """
        await self.add_to_server(serverID, entryNum, linkName)
        await self.add_to_user(userID, entryNum, linkName)
        await self.add_total_fixed(entryNum, linkName)