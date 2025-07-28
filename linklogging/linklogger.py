import asyncio
import json

class LinkLogger:
    def __init__(self):
        self.filepath = "linklogging/log.json"
        self.lock = asyncio.Lock()
        self.data = {}
        self.links = ["twitter", "instagram"]

    async def load(self):
        """
        Load the logger data from the JSON file.
        """
        async with self.lock:
            with open(self.filepath, "r") as f:
                self.data = json.load(f)

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
        """
        Get aggregated statistics across all link types.
        
        Returns
        -------
        tuple
            A tuple containing:
            - A dictionary of server IDs and their total counts.
            - A dictionary of user IDs and their total counts.
            - The total number of fixed links across all link types.
        """
        async with self.lock:
            # Aggregate stats across all link types
            server_totals = {}
            user_totals = {}
            total_fixed = 0

            for linkName in self.links:
                # Servers
                for serverID, count in self.data[linkName]["servers"].items():
                    server_totals[serverID] = server_totals.get(serverID, 0) + count
                # Users
                for userID, count in self.data[linkName]["users"].items():
                    user_totals[userID] = user_totals.get(userID, 0) + count
                # Total fixed
                total_fixed += self.data[linkName]["links_fixed"]

            sorted_servers = dict(sorted(server_totals.items(), key=lambda item: item[1], reverse=True))
            sorted_users = dict(sorted(user_totals.items(), key=lambda item: item[1], reverse=True))

            return sorted_servers, sorted_users, total_fixed

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
        for linkName in self.links:
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
        for linkName in self.links:
            userID = str(userID)
            async with self.lock:
                if userID not in self.data[linkName]["users"]:
                    pass
                else:
                    count += self.data[linkName]["users"][userID]
        return count

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