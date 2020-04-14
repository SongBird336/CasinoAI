import pydealer
import copy


class TreeNode:

    def __init__(self, gameBoard, aiHand, cardsPlayed, play, parent):
        #[0] = table, [1] = single builds. [2] = multi builds
        self.gameBoard = gameBoard
        self.aiHand = aiHand
        self.cardsPlayed = cardsPlayed
        self.play = play
        self.value = 0
        self.probability = 1
        self.parent = parent
        self.children = []

    def addChildren(self, children):
        if type(children) is not list:
            children = [children]
        self.children.extend(children)



class AI:
    """Class for managing the AI for Casino.py"""
    def __init__(self, gameBoard, hand, cardsPlayed):
        self.gameBoard = gameBoard
        self.hand = hand
        self.cardsPlayed = cardsPlayed

    def __findCombinations(self, table, value):
        combinations = []

        for i, card in enumerate(table):
            if self.__getCardValue(card.value) > value:
                continue
            elif self.__getCardValue(card.value) == value:
                combinations.append("/" + pydealer.card.card_abbrev(card.value, card.suit))
                combinations.extend(self.__findCombinations(table[i+1:], value))
            elif i < table.size - 1:
                subCombinations = self.__findCombinations(table[i+1], value - self.__getCardValue(card.value))
                if subCombinations is not None:
                    for combo in subCombinations:
                        combinations.append("/" + pydealer.card.card_abbrev(card.value, card.suit) + "/" + combo)

        if len(combinations) > 0:
            return combinations
        else:
            return None

    def __getPlayValue(self, play):
        cards = play.split("/")
        value = 0

        for card in cards:
            # If it's a play indicator, skip
            if card[0] == "T" or card[0] == "C" or card[0] == "B":
                continue

            if card == "10D":
                value += 10
            elif card[-1] == "S":
                if card[0] == "A" or card[0] == "2":
                    value += 6
                else:
                    value += 2
            elif card[0] == "A":
                value += 5
            else:
                value += 1


        return value

    def __findBestCapture(self, gameBoard, hand, forBuilds=False):
        table = gameBoard[0]
        
        combinations = []
        for card in hand:
            plays = self.__findCombinations(table, self.__getCardValue(card.value))
            # For each play, add the card used for the play at the frot of the play string
            for i, play in enumerate(plays):
                plays[i] = pydealer.card.card_abbrev(card.value, card.suit) + "/" + plays[i]
                if self.__getCardValue(card.value) in gameBoard[1]:
                        plays[i] += "/SB" + str(self.__getCardValue(card.value))

            if not forBuilds:
                # Check if builds can be captured, add to the end of each combo
                for i, play in enumerate(plays):
                    # Add the C to the front. We only want this if the function is called by itself,
                    # not when it's helping find builds
                    plays[i] = "C" + plays[i]

                    
                    if self.__getCardValue(card.value) in gameBoard[2]:
                        plays[i] += "/MB" + str(self.__getCardValue(card.value))
                # add to end of plays for just capturing builds
                if self.__getCardValue(card.value) in gameBoard[1] and self.__getCardValue(card.value) in gameBoard[2]:
                    plays.append("C/%s/SB%d/MB%d" % (pydealer.card.card_abbrev(card.value, card.suit), self.__getCardValue(card.value), self.__getCardValue(card.value)))
                elif self.__getCardValue(card.value) in gameBoard[2]:
                    plays.append("C/"+ pydealer.card.card_abbrev(card.value, card.suit) +"/MB" + str(self.__getCardValue(card.value)))
            if self.__getCardValue(card.value) in gameBoard[1]:
                plays.append("C/"+ pydealer.card.card_abbrev(card.value, card.suit) +"/SB" + str(self.__getCardValue(card.value)))

            combinations.extend(plays)
        
        # If no combinations found, trail first card of hand
        if len(combinations) == 0:
            return "T/%s/0" % (pydealer.card.card_abbrev(hand[0].value, hand[0].suit))

        # otherwise, figure out the best combo and return that
        index = 0
        maximum = 0
        for i, play in enumerate(combinations):
            value = self.__getPlayValue(play)
            if value > maximum:
                maximum = value
                index = i
        
        if not forBuilds:
            return combinations[index] + "/" + str(maximum)
        else:
            return combinations[index]

    def __findBestBuild(self, gameBoard, hand):
        return ""

    def __createNewTreeNode(self, parent, play, playerMove=False):
        # copy current gamestate
        gameBoard = copy.deepcopy(parent.gameBoard)
        hand = copy.deepcopy(parent.aiHand)
        cardsPlayed = copy.deepcopy(parent.cardsPlayed)

        # Change gamestate to reflect the play
        self.playCard(play, gameBoard, hand, cardsPlayed, playerMove=playerMove)

        # create new node for this play
        return TreeNode(gameBoard, hand, cardsPlayed, play, parent)

    def __getValueName(self, value):
        if value >= 2 and value <= 10:
            return str(value)
        elif value == 1:
            return "A"
        elif value == 11:
            return "J"
        elif value == 12:
            return "Q"
        elif value == 13:
            return "K"
        else:
            return "Something went wrong"

    def __getCardValue(self, value):
        if value == "Ace" or value == "ace" or value == "A" or value == "a":
            value = 1
        elif value == "Jack" or value == "jack" or value == "J" or value == "j":
            value = 11
        elif value == "Queen" or value == "queen" or value == "Q" or value == "q":
            value = 12
        elif value == "King" or value == "king" or value == "K" or value == "k":
            value = 13
        else:
            value = int(value)

        return value

    def __buildTree(self, parent):
        # Find the best capture and build given the current gamestate
        # If capture or build isn't possible, each method returns
        # A card to trail
        bestCapture = self.__findBestCapture(parent.gameBoard, parent.aiHand)
        bestBuild = self.__findBestBuild(parent.gameBoard, parent.aiHand)

        children = []

        # If Builds 
        if bestCapture[0] == "T" and bestBuild[0] == "T":
            children.append(self.__createNewTreeNode(parent, bestCapture))
        else:
            if bestCapture[0] != "T":
                children.append(self.__createNewTreeNode(parent, bestCapture))
            if bestBuild[0] != "T":
                children.append(self.__createNewTreeNode(parent, bestBuild))

        parent.addChildren(children)

        # If the last card played was the last one in the AI's hand, tally points and return
        # (This is the termination condition for our recursive loop)
        if parent.aiHand.size <= 1:
            for node in children:
                node.value = node.play.split("/")[-1]
            return
        # Otherwise, figure out player's moves, and continue building the tree
        else:
            # for each possible move
            for node in children:
                # for each possible card in the player's hand
                for value in range(1, 13):
                    # If all of the cards of this value have been played already, skip 
                    if len(node.cardsPlayed.find(self.__getValueName(value))) == 4:
                        continue
                    # Otherwise, get a card of that value into a dummy hand
                    deck = pydealer.Deck()
                    hand = pydealer.Stack()
                    hand.add(deck.get(self.__getValueName(value) + "H"))

                    # Find the best capture the player could make with this card
                    play = self.__findBestCapture(node.gameBoard, hand)

                    newNode = self.__createNewTreeNode(node, play, playerMove=True)
                    newNode.probability = (4 - node.cardsPlayed.find(self.__getValueName(value))) / (52 - node.cardsPlayed.size)
                    self.__buildTree(newNode)

                    # figure out the value of this node (the greater value of it's children)
                    maximum = newNode.children[0].value
                    if (len(newNode.children) > 1):
                        if newNode.children[1].value > maximum:
                            maximum = newNode.children[1].value

                    newNode.value = maximum

                    # add node to it's parent
                    node.addChildren(newNode)
                
                # Once all player options have been considered, calculate the expected value of the node
                expectedValue = 0.0
                for child in node.children:
                    expectedValue += child.value * child.probability
                node.value = expectedValue + node.play.split("/")[-1]
                


    def getNextMove(self, gameBoard, hand, cardsPlayed):
        
        newGameBoard = copy.deepcopy(gameBoard)
        newHand = copy.deepcopy(hand)
        newCardsPlayed = copy.deepcopy(cardsPlayed)

        root = TreeNode(newGameBoard, newHand, newCardsPlayed, None, None)

        self.__buildTree(root)

        
    def playCard(self, play, gameBoard, hand, cardsPlayed, playerMove=False):
        return ""

