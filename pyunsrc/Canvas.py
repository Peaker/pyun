from pygame import Rect

class Error(Exception): pass
class EntryAlreadyExists(Error): pass


class Object(object):
    def __init__(self):
        super(Object, self).__init__()
    def bounding_rect(self):
        raise NotImplementedError()

class Circle(Object):
    def __init__(self, position, diameter):
        super(Object, self).__init__()
        self.position = position
        self.diameter = diameter
    def bounding_rect(self):
        x, y = self.position
        return Rect((x - self.diameter/2, y - self.diameter/2),
                    (self.diameter, self.diameter))
    def collides_with(self, other):
        assert isinstance(other, Circle)
        sqr_diameter = ((self.diameter + other.diameter) / 2)**2
        x1, y1 = self.position
        x2, y2 = other.position
        return (x1-x2)**2 + (y1-y2)**2 <= sqr_diameter

class Canvas(object):
    def __init__(self, size, slot_size):
        self.area_rect = Rect((0,0), size)
        self.slot_size = slot_size
        self._rects_of_slot = {}
        self._slots_of_entry = {}

    def _slot_keys_of_rect(self, rect):
        slot_width, slot_height = self.slot_size
        for x in xrange(rect.left//slot_width, 1+rect.right//slot_width):
            for y in xrange(rect.top//slot_height, 1+rect.bottom//slot_height):
                yield x, y
        
    def _add(self, rect, entry):
        if entry in self._slots_of_entry:
            raise EntryAlreadyExists("Entry already in Canvas")
        assert entry not in self._slots_of_entry
        
        assert self.area_rect.contains(rect)

        self._slots_of_entry[entry] = slots = []
        for slot_key in self._slot_keys_of_rect(rect):
            self._rects_of_slot.setdefault(slot_key, {})[entry] = rect
            slots.append(slot_key)

    def add(self, entry):
        self._add(entry.bounding_rect(), entry)

    def remove(self, entry):
        for slot_key in self._slots_of_entry[entry]:
            del self._rects_of_slot[slot_key][entry]
        del self._slots_of_entry[entry]

    def clear(self):
        self._rects_of_slot.clear()
        self._slots_of_entry.clear()

    def _rect_collisions(self, rect):
        for slot_key in self._slot_keys_of_rect(rect):
            for entry, cur_rect in self._rects_of_slot.get(slot_key, {}).iteritems():
                if rect.colliderect(cur_rect):
                    yield entry
    
    def collisions(self, entry):
        for other_entry in self._rect_collisions(entry.bounding_rect()):
            if entry.collides_with(other_entry):
                yield other_entry

    def items(self):
        return self._slots_of_entry.iterkeys()
